"""Policy Specialist Sub-Agent implementation."""
from google.adk.agents import LlmAgent
from agents import config, prompts
from tools.policy_tool import list_concepts, read_concept


def create_policy_subagent() -> LlmAgent:
    """Instantiate the Policy Specialist Sub-Agent."""
    return LlmAgent(
        name="policy_specialist",
        model=config.GEMINI_MODEL,
        description="Specialist in HR policy documents, benefits, leave rules, and employee guidelines.",
        instruction=prompts.POLICY_SPECIALIST_PROMPT,
        tools=[list_concepts, read_concept],
    )
