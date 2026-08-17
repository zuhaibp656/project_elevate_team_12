"""ServiceImmediately ITSM Specialist Sub-Agent implementation."""
from google.adk.agents import LlmAgent
from agents import config, prompts
from tools.serviceimmediately_tools import (
    list_tickets,
    get_ticket_details,
    create_ticket,
    add_ticket_comment,
    update_ticket_status,
)


def create_itsm_subagent() -> LlmAgent:
    """Instantiate the ServiceImmediately ITSM Specialist Sub-Agent with live platform tools."""
    tools = [
        list_tickets,
        get_ticket_details,
        create_ticket,
        add_ticket_comment,
        update_ticket_status,
    ]

    return LlmAgent(
        name="itsm_specialist",
        model=config.GEMINI_MODEL,
        description="Specialist in ServiceImmediately ITSM incident tickets, status tracking, and comments.",
        instruction=prompts.ITSM_SPECIALIST_PROMPT,
        tools=tools,
    )
