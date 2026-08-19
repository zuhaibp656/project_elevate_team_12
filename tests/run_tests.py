"""Automated Test Runner executing all unit & integration test suites."""
import os
import sys
import unittest

# Ensure repo root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tests.test_policy_tool import test_list_concepts_structure, test_read_concept_grounding, test_hot_reload_atomic_cache
from tests.test_security_dlp import (
    test_nric_sanitization,
    test_credit_card_sanitization,
    test_credential_sanitization,
    test_model_armor_prompt_injection_defense,
    test_model_armor_safe_prompt_pass,
    test_gdpr_right_to_be_forgotten_purge
)
from tests.test_agent_routing import test_agent_hierarchy_and_subagents, test_subagent_tool_bindings
from tests.test_api_endpoints import test_health_check, test_w3c_distributed_tracing_propagation, test_hub_endpoint_dynamic_structure


def run_all_tests():
    print("=" * 70)
    print(" 🚀 RUNNING AUTOMATED AGENTIC TEST SUITE (TEAM 12)")
    print("=" * 70)
    
    test_cases = [
        ("Policy Tool Structure", test_list_concepts_structure),
        ("Policy Grounding & Citations", test_read_concept_grounding),
        ("Policy Hot-Reload Atomic Cache", test_hot_reload_atomic_cache),
        ("Security: NRIC In-Flight Masking", test_nric_sanitization),
        ("Security: Credit Card Masking", test_credit_card_sanitization),
        ("Security: Credential Redaction", test_credential_sanitization),
        ("Security: Model Armor Prompt Injection Defense", test_model_armor_prompt_injection_defense),
        ("Security: Model Armor Safe Prompt Invariant", test_model_armor_safe_prompt_pass),
        ("Security: GDPR Right to be Forgotten", test_gdpr_right_to_be_forgotten_purge),
        ("Multi-Agent Hierarchy & Sub-Agents", test_agent_hierarchy_and_subagents),
        ("Sub-Agent Domain Tool Bindings", test_subagent_tool_bindings),
        ("FastAPI Health Endpoint", test_health_check),
        ("W3C Distributed Tracing Headers", test_w3c_distributed_tracing_propagation),
        ("Dynamic FastMCP Hub Data Decoding", test_hub_endpoint_dynamic_structure),
    ]
    
    passed = 0
    failed = 0
    
    for name, func in test_cases:
        try:
            func()
            print(f"  [✓ PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [✗ FAIL] {name}: {str(e)}")
            failed += 1
            
    print("-" * 70)
    print(f" Test Results: {passed} Passed, {failed} Failed (Total: {len(test_cases)})")
    print("=" * 70)
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
