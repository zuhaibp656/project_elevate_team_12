"""FastAPI Backend Server bridging the Web UI Wrapper to the Multi-Agent Orchestrator."""
import os
import sys
from pathlib import Path
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
from agents.orchestrator import run_query
from agents.subagents.policy_subagent import create_policy_subagent
from agents.subagents.hcm_subagent import create_hcm_subagent
from agents.subagents.itsm_subagent import create_itsm_subagent
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

class ChatResponse(BaseModel):
    response: str
    mode: str
    status: str = "success"

# Pre-instantiate single-domain agents and runners for direct subagent routing
_session_service = InMemorySessionService()
_policy_agent = create_policy_subagent()
_hcm_agent = create_hcm_subagent()
_itsm_agent = create_itsm_subagent()

_runners = {
    "policy": Runner(app_name="policy_app", agent=_policy_agent, session_service=_session_service),
    "hcm": Runner(app_name="hcm_app", agent=_hcm_agent, session_service=_session_service),
    "itsm": Runner(app_name="itsm_app", agent=_itsm_agent, session_service=_session_service),
}

async def _run_single_agent(agent_key: str, prompt: str, user_id: str = "learner", session_id: str = "ui_session") -> str:
    runner = _runners[agent_key]
    app_name = f"{agent_key}_app"
    try:
        await _session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    except Exception:
        pass  # session already exists
    
    msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    res_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=msg):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    res_text += part.text
    return res_text or "No response generated."

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty query message.")
    
    mode = req.mode.lower()
    try:
        if mode in ("policy", "hcm", "itsm"):
            ans = await _run_single_agent(mode, req.message)
        else:
            # Auto multi-agent orchestrator
            ans = await run_query(req.message)
            mode = "auto"
        
        return ChatResponse(response=ans, mode=mode, status="success")
    except Exception as e:
        return ChatResponse(
            response=f"An error occurred while processing your request: {str(e)}",
            mode=mode,
            status="error"
        )

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
