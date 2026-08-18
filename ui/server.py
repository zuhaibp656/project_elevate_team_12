"""FastAPI Backend Server bridging the Web UI Wrapper to the Multi-Agent Orchestrator."""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

class ChatRequest(BaseModel):
    message: str
    mode: str = "auto"  # "auto", "policy", "hcm", "itsm"

class TraceItem(BaseModel):
    tool: str
    payload: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    response: str
    mode: str
    trace: List[TraceItem] = []
    status: str = "success"

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

async def _run_single_agent(agent_key: str, prompt: str, user_id: str = "learner", session_id: str = "ui_session"):
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

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty query message.")
    
    mode = req.mode.lower()
    try:
        if mode in ("policy", "hcm", "itsm"):
            ans, evidence = await _run_single_agent(mode, req.message)
        else:
            ans, evidence = await run_query_traced_async(req.message)
            mode = "auto"
        
        trace_items = [
            TraceItem(tool=e.get("tool", "unknown"), payload=e.get("payload", {}) if isinstance(e.get("payload"), dict) else {"result": str(e.get("payload"))})
            for e in evidence
        ]
        
        return ChatResponse(response=ans, mode=mode, trace=trace_items, status="success")
    except Exception as e:
        return ChatResponse(
            response=f"An error occurred while processing your request: {str(e)}",
            mode=mode,
            trace=[],
            status="error"
        )

@app.get("/api/hub")
async def get_hub_data():
    """Fetch live data from FastMCP servers for the user hub drawer."""
    emp_id = "EMP-380"
    
    # 1. Balances
    raw_bal = get_employee_balances(emp_id)
    # Parse balances (Vacation 15/20, Sick 10/10)
    vacation_rem, vacation_total, vacation_used = 15.0, 20.0, 5.0
    sick_rem, sick_total, sick_used = 10.0, 10.0, 0.0
    
    # 2. Personal Info
    raw_profile = get_personal_info(emp_id)
    
    # 3. Tickets
    raw_tickets = list_tickets(emp_id)
    tickets_list = []
    try:
        if isinstance(raw_tickets, str):
            tickets_list = json.loads(raw_tickets)
        elif isinstance(raw_tickets, list):
            tickets_list = raw_tickets
    except Exception:
        pass
    
    # 4. Leave requests
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
        "name": "Zuhaibp Employee",
        "role": "Senior Cloud Engineer",
        "department": "Engineering & Innovation",
        "balances": {
            "vacation": {"remaining": vacation_rem, "total": vacation_total, "used": vacation_used},
            "sick": {"remaining": sick_rem, "total": sick_total, "used": sick_used},
            "raw": raw_bal
        },
        "profile": {
            "address": "Singapore Office, 80 Pasir Panjang Rd, Singapore",
            "phone": "+65-6521-0000",
            "raw": raw_profile
        },
        "tickets": tickets_list,
        "leave_requests": leave_list
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

def start_server(host: str = "127.0.0.1", port: int = 8090):
    uvicorn.run("ui.server:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    start_server()
