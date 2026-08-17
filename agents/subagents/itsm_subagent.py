"""ServiceImmediately ITSM Specialist Sub-Agent implementation."""
from google.adk.agents import LlmAgent
from agents import config, prompts
from tools.mcp_toolsets import create_serviceimmediately_mcp_toolset


def create_itsm_subagent() -> LlmAgent:
    """Instantiate the ServiceImmediately ITSM Specialist Sub-Agent."""
    serviceimmediately_mcp = create_serviceimmediately_mcp_toolset()
    return LlmAgent(
        name="itsm_specialist",
        model=config.GEMINI_MODEL,
        description="Specialist in ServiceImmediately ITSM incident tickets, status tracking, and comments.",
        instruction=prompts.ITSM_SPECIALIST_PROMPT,
        tools=[serviceimmediately_mcp],
    )
