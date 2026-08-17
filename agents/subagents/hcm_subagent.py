"""WorkWeek HCM Specialist Sub-Agent implementation."""
from google.adk.agents import LlmAgent
from agents import config, prompts
from tools.mcp_toolsets import create_workweek_mcp_toolset


def create_hcm_subagent() -> LlmAgent:
    """Instantiate the WorkWeek HCM Specialist Sub-Agent."""
    workweek_mcp = create_workweek_mcp_toolset()
    return LlmAgent(
        name="hcm_specialist",
        model=config.GEMINI_MODEL,
        description="Specialist in WorkWeek HCM operations (profiles, leave balances, and time-off requests).",
        instruction=prompts.HCM_SPECIALIST_PROMPT,
        tools=[workweek_mcp],
    )
