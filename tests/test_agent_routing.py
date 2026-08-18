"""Automated tests validating multi-agent subagent definitions and tools."""
from agents.subagents.policy_subagent import create_policy_subagent
from agents.subagents.hcm_subagent import create_hcm_subagent
from agents.subagents.itsm_subagent import create_itsm_subagent
from agents.orchestrator import create_orchestrator_agent


def test_agent_hierarchy_and_subagents():
    """Verify root orchestrator declares all 3 specialist subagents."""
    root = create_orchestrator_agent()
    assert root.name == "hr_orchestrator"
    assert len(root.sub_agents) == 3
    
    subagent_names = [sa.name for sa in root.sub_agents]
    assert "policy_specialist" in subagent_names
    assert "hcm_specialist" in subagent_names
    assert "itsm_specialist" in subagent_names


def test_subagent_tool_bindings():
    """Verify each specialist subagent has correct domain tools attached."""
    policy_sa = create_policy_subagent()
    hcm_sa = create_hcm_subagent()
    itsm_sa = create_itsm_subagent()
    
    policy_tool_names = [t.__name__ for t in policy_sa.tools]
    hcm_tool_names = [t.__name__ for t in hcm_sa.tools]
    itsm_tool_names = [t.__name__ for t in itsm_sa.tools]
    
    assert "list_concepts" in policy_tool_names
    assert "read_concept" in policy_tool_names
    
    assert "get_employee_balances" in hcm_tool_names
    assert "request_time_off" in hcm_tool_names
    
    assert "list_tickets" in itsm_tool_names
    assert "create_ticket" in itsm_tool_names
    assert "escalate_to_human_hr" in itsm_tool_names
