"""WorkWeek HCM Specialist Sub-Agent implementation."""
from google.adk.agents import LlmAgent
from agents import config, prompts
from tools.workweek_tools import (
    get_current_employee_id,
    get_employee_balances,
    request_time_off,
    get_personal_info,
    update_personal_info,
    get_leave_requests,
    cancel_leave_request,
)


def create_hcm_subagent() -> LlmAgent:
    """Instantiate the WorkWeek HCM Specialist Sub-Agent with live platform tools."""
    tools = [
        get_current_employee_id,
        get_employee_balances,
        request_time_off,
        get_personal_info,
        update_personal_info,
        get_leave_requests,
        cancel_leave_request,
    ]

    return LlmAgent(
        name="hcm_specialist",
        model=config.GEMINI_MODEL,
        description="Specialist in WorkWeek HCM operations (employee profiles, leave balances, time-off requests, and contact info).",
        instruction=prompts.HCM_SPECIALIST_PROMPT,
        tools=tools,
    )
