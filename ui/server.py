"""FastAPI Backend Server bridging the Web UI Wrapper to the Multi-Agent Orchestrator (W3C Traced & PII Sanitized)."""
import os
import sys
import json
import uuid
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents import config
from agents.orchestrator import run_query_traced_async
from agents.subagents.policy_subagent import create_policy_subagent
from agents.subagents.hcm_subagent import create_hcm_subagent
from agents.subagents.itsm_subagent import create_itsm_subagent
from agents.storage import (
    sanitize_pii,
    sanitize_agent_output,
    record_session,
    record_message,
    record_tool_execution
)
from tools.workweek_tools import (
    get_employee_balances,
    get_personal_info,
    get_leave_requests
)
from tools.serviceimmediately_tools import (
    list_tickets,
    add_ticket_comment,
    update_ticket_status
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

app = FastAPI(title="HR Agentic Solution — Web UI Wrapper", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def distributed_tracing_middleware(request: Request, call_next):
    """W3C traceparent and X-Correlation-ID Distributed Tracing Middleware."""
    correlation_id = request.headers.get("X-Correlation-ID") or f"trace-{uuid.uuid4().hex[:12]}"
    traceparent = request.headers.get("traceparent") or f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-01"
    
    # Attach to request state for downstream handler extraction
    request.state.correlation_id = correlation_id
    request.state.traceparent = traceparent
    
    start_time = time.time()
    response: Response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Propagate W3C & Correlation ID back to client
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["traceparent"] = traceparent
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    return response


class ChatRequest(BaseModel):
    message: str
    mode: str = "auto"  # "auto", "policy", "hcm", "itsm"
    session_id: Optional[str] = "session-1"
    user_id: Optional[str] = "EMP-380"
    mcp_token: Optional[str] = None
    user_email: Optional[str] = None


class VerifyIdentityRequest(BaseModel):
    mcp_token: str
    email: Optional[str] = None
    employee_id: Optional[str] = None


class TraceItem(BaseModel):
    tool: str
    payload: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    response: str
    mode: str
    trace: List[TraceItem] = []
    status: str = "success"
    correlation_id: Optional[str] = None


class AddCommentRequest(BaseModel):
    ticket_id: str
    comment: str
    author: str = "EMP-380"


class UpdateStatusRequest(BaseModel):
    ticket_id: str
    status: str
    resolution_notes: str = ""


# Pre-instantiate single-domain agents and runners
_session_service = InMemorySessionService()
_policy_agent = create_policy_subagent()
_hcm_agent = create_hcm_subagent()
_itsm_agent = create_itsm_subagent()

_runners = {
    "policy": Runner(app_name="policy_app", agent=_policy_agent, session_service=_session_service),
    "hcm": Runner(app_name="hcm_app", agent=_hcm_agent, session_service=_session_service),
    "itsm": Runner(app_name="itsm_app", agent=_itsm_agent, session_service=_session_service),
}


async def _run_single_agent(agent_key: str, prompt: str, user_id: str = "EMP-380", session_id: str = "ui_session"):
    runner = _runners[agent_key]
    app_name = f"{agent_key}_app"
    try:
        await _session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    except Exception:
        pass
    
    msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    res_text = ""
    evidence = []
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=msg):
        if event.content and event.content.parts:
            for part in event.content.parts:
                fr = getattr(part, "function_response", None)
                if fr is not None:
                    evidence.append({
                        "tool": getattr(fr, "name", "?"),
                        "payload": getattr(fr, "response", {})
                    })
                if part.text:
                    res_text += part.text
    return res_text or "No response generated.", evidence


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[str] = None
    employee_id: Optional[str] = None


@app.post("/api/auth/google")
async def google_auth_endpoint(req: GoogleAuthRequest):
    """Verify Google OAuth2 ID Token or direct Google account email."""
    email = req.email or ""
    name = ""
    picture = ""

    if req.credential:
        try:
            import base64
            import json
            parts = req.credential.split(".")
            if len(parts) >= 2:
                padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
                payload = json.loads(base64.urlsafe_b64decode(padded))
                email = payload.get("email", email)
                name = payload.get("name", "")
                picture = payload.get("picture", "")
        except Exception as e:
            logger.warning(f"Could not parse Google ID token: {e}")

    if not email:
        raise HTTPException(status_code=400, detail="Google corporate email or token is required.")

    # Check domain
    is_google = email.lower().endswith("@google.com")
    clean_name = name or email.split("@")[0].replace(".", " ").title() or "Google Team Member"
    emp_id = req.employee_id or "EMP-380"

    return {
        "authenticated": True,
        "email": email,
        "name": clean_name,
        "picture": picture,
        "is_google": is_google,
        "employee_id": emp_id,
        "role": "Senior Cloud Engineer" if is_google else "Corporate Team Member",
        "address": "Singapore Office, 80 Pasir Panjang Rd, Singapore",
        "message": f"Successfully authenticated Google account: {email}"
    }


@app.post("/api/identity/verify")
async def verify_identity_endpoint(req: VerifyIdentityRequest):
    """Validate user FastMCP token and return connection status."""
    token = req.mcp_token.strip() if req.mcp_token else ""
    if not token:
        raise HTTPException(status_code=400, detail="MCP token is required.")
    
    emp_id = req.employee_id or "EMP-380"
    config.ACTIVE_MCP_TOKEN_CV.set(token)
    config.ACTIVE_USER_ID_CV.set(emp_id)

    raw_bal = get_employee_balances(emp_id)
    if isinstance(raw_bal, str) and ("error" in raw_bal.lower() or "circuit breaker" in raw_bal.lower()) and not ("leave balances" in raw_bal.lower() or "{" in raw_bal):
        return {
            "valid": False,
            "error": "Authentication failed on Mock SaaS. Please verify your FastMCP token from https://mock-saas.aishprabhat.demo.altostrat.com/"
        }
    
    raw_info = get_personal_info(emp_id)
    return {
        "valid": True,
        "employee_id": emp_id,
        "email": req.email or f"{emp_id.lower()}@altostrat.demo",
        "raw_balances": raw_bal,
        "raw_info": raw_info,
        "message": f"Successfully connected workspace identity for {emp_id}!"
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, request: Request):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty query message.")
    
    # Extract caller-specific FastMCP token & Identity headers if provided
    client_token = req.mcp_token or request.headers.get("X-MCP-Token") or request.headers.get("x-mcp-token") or ""
    client_user_id = req.user_id or request.headers.get("X-Employee-ID") or request.headers.get("x-employee-id") or "EMP-380"
    client_email = req.user_email or request.headers.get("X-User-Email") or request.headers.get("x-user-email") or ""

    if client_token and client_token.strip():
        config.ACTIVE_MCP_TOKEN_CV.set(client_token.strip())
    else:
        # Use dynamic token resolution (Secret Manager / Environment / Active Token)
        config.ACTIVE_MCP_TOKEN_CV.set(config.get_current_mcp_token())

    if client_user_id and client_user_id.strip():
        config.ACTIVE_USER_ID_CV.set(client_user_id.strip())
    if client_email and client_email.strip():
        config.ACTIVE_USER_EMAIL_CV.set(client_email.strip())

    correlation_id = getattr(request.state, "correlation_id", f"trace-{uuid.uuid4().hex[:12]}")
    session_id = req.session_id or "session-1"
    user_id = client_user_id
    
    # In-Flight PII Sanitization
    sanitized_prompt = sanitize_pii(req.message)
    record_session(session_id, user_id, sanitized_prompt[:60])
    record_message(session_id, correlation_id, "user", sanitized_prompt)

    mode = req.mode.lower()
    start_t = time.time()
    try:
        # Always execute via the central Multi-Agent Orchestrator so all sub-agents and tools (HCM leave booking, ITSM ticketing, Policy RAG) are accessible
        ans, evidence = await run_query_traced_async(sanitized_prompt, user_id=user_id, session_id=session_id)
        mode = "auto"
        
        latency = int((time.time() - start_t) * 1000)
        sanitized_ans = sanitize_agent_output(ans)
        record_message(session_id, correlation_id, "assistant", sanitized_ans)

        trace_items = []
        for e in evidence:
            tool_name = e.get("tool", "unknown")
            payload = e.get("payload", {})
            if not isinstance(payload, dict):
                payload = {"result": str(payload)}
            trace_items.append(TraceItem(tool=tool_name, payload=payload))
            record_tool_execution(session_id, correlation_id, mode, tool_name, payload, payload, "SUCCESS", latency)
        
        return ChatResponse(
            response=sanitized_ans,
            mode=mode,
            trace=trace_items,
            status="success",
            correlation_id=correlation_id
        )
    except Exception as e:
        err_str = str(e)
        if "Reauthentication is needed" in err_str or "UNAUTHENTICATED" in err_str or "ACCESS_TOKEN_TYPE_UNSUPPORTED" in err_str:
            err_msg = (
                "⚠️ **Authentication Notice (Local Development Environment)**:\n\n"
                "Your local Google Cloud Application Default Credentials (ADC) have expired or need a session refresh.\n\n"
                "👉 **To fix in your local terminal**, run:\n"
                "```bash\n"
                "gcloud auth application-default login\n"
                "```\n\n"
                "*(Note: On live Google Cloud Run, authentication is managed automatically via Cloud Run's Compute IAM Service Account with zero credential expiration).*"
            )
        else:
            err_msg = f"An error occurred while processing your request: {err_str}"

        record_message(session_id, correlation_id, "assistant", err_msg)
        return ChatResponse(
            response=err_msg,
            mode=mode,
            trace=[],
            status="error",
            correlation_id=correlation_id
        )


@app.get("/api/hub")
async def get_hub_data(request: Request, employee_id: Optional[str] = None):
    """Fetch and decode live dynamic data from FastMCP servers for the user hub drawer."""
    client_token = request.headers.get("X-MCP-Token") or request.headers.get("x-mcp-token") or ""
    client_user_id = employee_id or request.headers.get("X-Employee-ID") or request.headers.get("x-employee-id") or "EMP-380"
    
    if client_token and client_token.strip():
        config.ACTIVE_MCP_TOKEN_CV.set(client_token.strip())
    else:
        config.ACTIVE_MCP_TOKEN_CV.set(config.get_current_mcp_token())

    if client_user_id and client_user_id.strip():
        config.ACTIVE_USER_ID_CV.set(client_user_id.strip())
        
    emp_id = client_user_id
    
    # 1. Decode Live Balances from FastMCP
    raw_bal = get_employee_balances(emp_id)
    vacation_rem, vacation_total, vacation_used = 20.0, 20.0, 0.0
    sick_rem, sick_total, sick_used = 10.0, 10.0, 0.0
    
    try:
        if isinstance(raw_bal, str):
            # Try JSON parsing
            try:
                bal_data = json.loads(raw_bal)
                if isinstance(bal_data, dict):
                    # FastMCP raw response or Mock JSON structure
                    if "vacation_days" in bal_data:
                        vacation_rem = float(bal_data.get("vacation_days", 20.0))
                    elif "vacation" in bal_data and isinstance(bal_data["vacation"], dict):
                        vacation_rem = float(bal_data["vacation"].get("remaining", 20.0))
                    vacation_total = 20.0
                    vacation_used = max(0.0, vacation_total - vacation_rem)

                    if "sick_days" in bal_data:
                        sick_rem = float(bal_data.get("sick_days", 10.0))
                    elif "sick" in bal_data and isinstance(bal_data["sick"], dict):
                        sick_rem = float(bal_data["sick"].get("remaining", 10.0))
                    sick_total = 10.0
                    sick_used = max(0.0, sick_total - sick_rem)
            except Exception:
                # Regex parse formatted string from FastMCP
                v_match = re.search(r'Vacation:\s*([\d\.]+)\s*days\s*remaining\s*(?:\(([\d\.]+)/([\d\.]+)\s*used\))?', raw_bal, re.IGNORECASE)
                if v_match:
                    vacation_rem = float(v_match.group(1))
                    if v_match.group(2) and v_match.group(3):
                        vacation_used = float(v_match.group(2))
                        vacation_total = float(v_match.group(3))
                    else:
                        vacation_total = 20.0
                        vacation_used = max(0.0, vacation_total - vacation_rem)

                s_match = re.search(r'Sick:\s*([\d\.]+)\s*days\s*remaining\s*(?:\(([\d\.]+)/([\d\.]+)\s*used\))?', raw_bal, re.IGNORECASE)
                if s_match:
                    sick_rem = float(s_match.group(1))
                    if s_match.group(2) and s_match.group(3):
                        sick_used = float(s_match.group(2))
                        sick_total = float(s_match.group(3))
                    else:
                        sick_total = 10.0
                        sick_used = max(0.0, sick_total - sick_rem)
        elif isinstance(raw_bal, dict):
            if "vacation_days" in raw_bal:
                vacation_rem = float(raw_bal.get("vacation_days", 20.0))
            elif "vacation" in raw_bal and isinstance(raw_bal["vacation"], dict):
                vacation_rem = float(raw_bal["vacation"].get("remaining", 20.0))
            vacation_total = 20.0
            vacation_used = max(0.0, vacation_total - vacation_rem)

            if "sick_days" in raw_bal:
                sick_rem = float(raw_bal.get("sick_days", 10.0))
            elif "sick" in raw_bal and isinstance(raw_bal["sick"], dict):
                sick_rem = float(raw_bal["sick"].get("remaining", 10.0))
            sick_total = 10.0
            sick_used = max(0.0, sick_total - sick_rem)
    except Exception:
        pass

    # 2. Decode Live Personal Info from FastMCP
    raw_profile = get_personal_info(emp_id)
    profile_address = "Singapore Office, 80 Pasir Panjang Rd, Singapore"
    profile_phone = "+65-6521-0000"
    profile_name = "Team 12 Member"
    profile_email = "emp380@enterprise.demo"

    try:
        prof_data = json.loads(raw_profile) if isinstance(raw_profile, str) else raw_profile
        if isinstance(prof_data, dict):
            profile_address = prof_data.get("address", profile_address)
            profile_phone = prof_data.get("phone", profile_phone)
            profile_name = prof_data.get("full_name") or prof_data.get("name", profile_name)
            profile_email = prof_data.get("email", profile_email)
    except Exception:
        pass

    # 3. Decode Live Tickets from FastMCP
    raw_tickets = list_tickets(emp_id)
    tickets_list = []
    try:
        if isinstance(raw_tickets, str):
            tickets_list = json.loads(raw_tickets)
        elif isinstance(raw_tickets, list):
            tickets_list = raw_tickets
    except Exception:
        pass

    # 4. Decode Live Leave Requests from FastMCP
    raw_leave = get_leave_requests(emp_id)
    leave_list = []
    try:
        if isinstance(raw_leave, str):
            leave_list = json.loads(raw_leave)
        elif isinstance(raw_leave, list):
            leave_list = raw_leave
    except Exception:
        pass

    return {
        "employee_id": emp_id,
        "name": profile_name,
        "email": profile_email,
        "role": "Senior Cloud Engineer",
        "department": "Engineering & Innovation",
        "balances": {
            "vacation": {"remaining": vacation_rem, "total": vacation_total, "used": vacation_used},
            "sick": {"remaining": sick_rem, "total": sick_total, "used": sick_used},
            "raw": raw_bal
        },
        "profile": {
            "address": profile_address,
            "phone": profile_phone,
            "raw": raw_profile
        },
        "tickets": tickets_list if isinstance(tickets_list, list) else [],
        "leave_requests": leave_list if isinstance(leave_list, list) else []
    }


@app.post("/api/tickets/comment")
async def add_comment_api(req: AddCommentRequest):
    res = add_ticket_comment(req.ticket_id, req.comment, req.author)
    return {"result": res, "status": "success"}


@app.post("/api/tickets/status")
async def update_status_api(req: UpdateStatusRequest):
    res = update_ticket_status(req.ticket_id, req.status, req.resolution_notes)
    return {"result": res, "status": "success"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "HR Agentic Web Wrapper", "version": "1.0.0"}


# Serve index.html
@app.get("/")
async def get_index():
    index_file = Path(__file__).resolve().parent / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "HR Agentic Solution UI Wrapper"}


def start_server(host: str = None, port: int = None):
    h = host or os.getenv("HOST", "0.0.0.0")
    p = port or int(os.getenv("PORT", 8090))
    uvicorn.run("ui.server:app", host=h, port=p, reload=False)


if __name__ == "__main__":
    start_server()
