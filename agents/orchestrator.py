"""Main Orchestrator Agent and Execution Runner."""
import asyncio
import sys
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from datetime import datetime, timezone
from tools.web_search_tool import web_search
from agents import config, prompts
from agents.subagents import (
    create_policy_subagent,
    create_hcm_subagent,
    create_itsm_subagent,
)


def create_orchestrator_agent() -> LlmAgent:
    """Instantiate the Central Orchestrator root agent with all sub-agents and web intelligence."""
    policy_subagent = create_policy_subagent()
    hcm_subagent = create_hcm_subagent()
    itsm_subagent = create_itsm_subagent()

    return LlmAgent(
        name="hr_orchestrator",
        model=config.GEMINI_MODEL,
        description="Central Intelligent HR Orchestrator managing self-service inquiries, cross-system workflows, and web intelligence.",
        instruction=prompts.ORCHESTRATOR_PROMPT,
        tools=[web_search],
        sub_agents=[policy_subagent, hcm_subagent, itsm_subagent],
    )


# Lazy-loaded root agent and session service
root_agent = create_orchestrator_agent()
_session_service = None


def _ensure_runner():
    global _session_service
    if _session_service is None:
        _session_service = InMemorySessionService()
    return Runner(app_name=config.APP_NAME, agent=root_agent, session_service=_session_service)


async def _run_query_traced_async(query: str, user_id: str = "learner", session_id: str = "session-1"):
    runner = _ensure_runner()
    try:
        await _session_service.create_session(
            app_name=config.APP_NAME, user_id=user_id, session_id=session_id
        )
    except Exception:
        pass  # Session already exists

    active_emp = user_id or config.get_current_user_id()
    active_email = config.ACTIVE_USER_EMAIL_CV.get()

    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    day_name = now.strftime("%A")

    context_parts = [
        f"Employee ID={active_emp or 'EMP-380'}",
        f"Email={active_email or 'emp380@enterprise.demo'}",
        f"Today's Date={today_str} ({day_name}, Operational Year=2026)"
    ]

    context_tag = f"[Authenticated Context: {', '.join(context_parts)}]\n"
    full_prompt = f"{context_tag}{query}" if not query.startswith("[Authenticated") else query

    message = types.Content(role="user", parts=[types.Part(text=full_prompt)])
    final_texts = []
    evidence = []

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=message
    ):
        if not (event.content and event.content.parts):
            continue
        for part in event.content.parts:
            fr = getattr(part, "function_response", None)
            if fr is not None:
                evidence.append({
                    "tool": getattr(fr, "name", "?"),
                    "payload": getattr(fr, "response", {})
                })
        if event.is_final_response() and event.content.parts:
            texts = [p.text for p in event.content.parts if getattr(p, "text", None)]
            if texts:
                final_texts.extend(texts)

    return "\n".join(final_texts), evidence


async def run_query_async(query: str, user_id: str = "learner", session_id: str = "session-1") -> str:
    """Run a query asynchronously and return the final text response."""
    answer, _evidence = await _run_query_traced_async(query, user_id=user_id, session_id=session_id)
    return answer


async def run_query_traced_async(query: str, user_id: str = "learner", session_id: str = "session-1"):
    """Run a query asynchronously and return (answer, evidence)."""
    return await _run_query_traced_async(query, user_id=user_id, session_id=session_id)


def run_query(query: str, user_id: str = "learner", session_id: str = "session-1") -> str:
    """Run a query synchronously and return the final text response."""
    answer, _evidence = asyncio.run(_run_query_traced_async(query, user_id=user_id, session_id=session_id))
    return answer


def run_query_traced(query: str, user_id: str = "learner", session_id: str = "session-1"):
    """Run a query synchronously and return (answer, evidence)."""
    return asyncio.run(_run_query_traced_async(query, user_id=user_id, session_id=session_id))


def _interactive():
    print(f"HR Centralized Orchestrator [{config.GEMINI_MODEL}] — type 'exit' to quit.")
    while True:
        try:
            q = input("\nyou > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"exit", "quit"}:
            break
        if q:
            print(f"\nagent > {run_query(q)}")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if argv and argv[0] == "--interactive":
        _interactive()
    elif argv:
        print(run_query(" ".join(argv)))
    else:
        print('Usage: ./deploy.sh --query "<question>"  |  --cli  |  --web')


if __name__ == "__main__":
    main()
