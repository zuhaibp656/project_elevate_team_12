"""Policy Specialist Sub-Agent implementation."""
from google.adk.agents import LlmAgent
from agents import config, prompts
from tools.policy_tool import list_concepts, read_concept
from tools.web_search_tool import web_search


def create_policy_subagent() -> LlmAgent:
    """Instantiate the Policy Specialist Sub-Agent."""
    return LlmAgent(
        name="policy_specialist",
        model=config.GEMINI_MODEL,
        description="Specialist in HR policy documents, benefits, statutory guidelines, MOM regulations, and web knowledge.",
        instruction=prompts.POLICY_SPECIALIST_PROMPT,
        tools=[list_concepts, read_concept, web_search],
    )
