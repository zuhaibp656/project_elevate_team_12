"""Centralized HR Agentic Solution (MVP 1).
Orchestrates Policy, WorkWeek, and ServiceImmediately via Sub-Agents.
"""
import asyncio
import sys

from google.adk.agents import LlmAgent
from . import subagents
from .tools import mcp_workweek
from .tools import mcp_service_immediately

# Mock retrieval tool for Policy (since we don't have the original `okf_tool` / `rag_tool` copied over yet)
def mock_retrieve_policy(query: str) -> str:
    """Query policy documents, retrieve relevant sections."""
    return "MOCK_POLICY: The company provides 10 days of medical leave. Home office monitor requires manager approval. For bereavement, you get 3 days off."

# Define the Sub-Agents
policy_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="policy_agent",
    description="HR Policy Specialist to answer policy questions.",
    instruction=subagents.POLICY_AGENT_PROMPT,
    tools=[mock_retrieve_policy]
)

hcm_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="hcm_agent",
    description="WorkWeek HCM Specialist to manage profiles and leaves.",
    instruction=subagents.HCM_AGENT_PROMPT,
    tools=[
        mcp_workweek.retrieve_employee_profile,
        mcp_workweek.update_contact_information,
        mcp_workweek.query_time_off_balances,
        mcp_workweek.submit_leave_request
    ]
)

itsm_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="itsm_agent",
    description="ServiceImmediately ITSM Specialist to manage IT tickets.",
    instruction=subagents.ITSM_AGENT_PROMPT,
    tools=[
        mcp_service_immediately.query_ticket_details,
        mcp_service_immediately.create_incident_ticket,
        mcp_service_immediately.post_ticket_comment,
        mcp_service_immediately.update_ticket_status
    ]
)

# Define the Orchestrator
ROOT_PROMPT = """You are the Centralized HR Orchestrator.
Your goal is to delegate user requests to the appropriate sub-agent:
- Policy queries -> policy_agent
- Leave/Profile management -> hcm_agent
- Ticket/IT issues -> itsm_agent
For Cross-System Orchestration (e.g. Relocation or Medical leave needing a ticket), coordinate with multiple sub-agents in a chain.
"""

root_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="hr_orchestrator",
    description="Centralized Orchestrator for HR Agentic Solution.",
    instruction=ROOT_PROMPT,
    tools=[policy_agent, hcm_agent, itsm_agent]
)

_session_service = None

def _ensure_runner():
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    global _session_service
    if _session_service is None:
        _session_service = InMemorySessionService()
    return Runner(app_name="hr_solution", agent=root_agent, session_service=_session_service)

async def _run_query_traced_async(query, user_id, session_id):
    from google.genai import types
    runner = _ensure_runner()
    await _session_service.create_session(app_name="hr_solution", user_id=user_id, session_id=session_id)
    
    message = types.Content(role="user", parts=[types.Part(text=query)])
    final = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
        if event.is_final_response() and event.content.parts:
            texts = [p.text for p in event.content.parts if getattr(p, "text", None)]
            if texts:
                final = "\n".join(texts)
    return final

def run_query(query: str, user_id: str = "emp_001", session_id: str = "session-1") -> str:
    return asyncio.run(_run_query_traced_async(query, user_id, session_id))

def _interactive():
    print("HR Orchestrator — type 'exit' to quit.")
    while True:
        try:
            q = input("\nyou > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"exit", "quit"}:
            break
        if q:
            print(f"\nagent > {run_query(q)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        _interactive()
    elif len(sys.argv) > 1:
        print(run_query(" ".join(sys.argv[1:])))
    else:
        print('Usage: python -m agent.agent "<question>"  |  --interactive')
