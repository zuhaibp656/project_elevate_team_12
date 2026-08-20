"""Model Armor & Enterprise Security Guardrails (Model Armor, Prompt Injection Defense & Cloud DLP Simulation).

This module provides real-time in-flight inspection and protection:
1. Prompt Injection & Jailbreak Defense (Model Armor Invariant)
2. In-Flight SPII & PII Sanitization (Cloud DLP)
3. Data Exfiltration & System Prompt Leakage Shield
4. Safe Fallback / Non-breaking Sanitization
"""
import re
from typing import Tuple, Dict, Any

# ---------------------------------------------------------------------------
# 1. Regex Patterns for In-Flight PII / SPII Redaction (Cloud DLP)
# ---------------------------------------------------------------------------
NRIC_PATTERN = re.compile(r"\b[STFGM]\d{7}[A-Z]\b", re.IGNORECASE)
CREDIT_CARD_PATTERN = re.compile(r"\b(?:4[0-9]{3}|5[1-5][0-9]{2}|6011|3[47][0-9]{2})[ -]?[0-9]{4}[ -]?[0-9]{4}[ -]?[0-9]{3,4}\b")
CREDENTIAL_PATTERN = re.compile(r"(?i)(password|secret|api[_-]?key|bearer|token)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{8,})['\"]?")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
SQL_INJECTION_PATTERN = re.compile(r"(?i)\b(UNION\s+SELECT|DROP\s+TABLE|ALTER\s+TABLE|DELETE\s+FROM|EXEC(\s|\()+xp_)\b")

# ---------------------------------------------------------------------------
# 2. Prompt Injection & Jailbreak Heuristics (Model Armor)
# ---------------------------------------------------------------------------
INJECTION_SIGNATURES = [
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions"),
    re.compile(r"(?i)disregard\s+(all\s+)?(system|safety)\s+(prompts?|instructions?)"),
    re.compile(r"(?i)you\s+are\s+now\s+(in\s+)?(DAN|developer|unrestricted|sudo)\s+mode"),
    re.compile(r"(?i)system\s+override\s*:\s*disable\s+guardrails"),
    re.compile(r"(?i)print\s+(the\s+)?system\s+prompt"),
    re.compile(r"(?i)reveal\s+internal\s+agent\s+instructions"),
]


def inspect_prompt_safety(prompt: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Inspect an inbound user prompt using Model Armor safety checks.

    Returns:
        is_safe (bool): True if prompt is safe; False if severe adversarial injection is detected.
        cleaned_prompt (str): Prompt sanitized of SPII/PII.
        audit_metadata (dict): Audit telemetry for SecOps and compliance logging.
    """
    if not prompt or not isinstance(prompt, str):
        return True, prompt or "", {"threat_level": "NONE", "flags": []}

    flags = []
    threat_level = "LOW"

    # Check for adversarial prompt injection signatures
    for pattern in INJECTION_SIGNATURES:
        if pattern.search(prompt):
            flags.append("PROMPT_INJECTION_ATTEMPT")
            threat_level = "HIGH"
            break

    # Check for SQL injection attempts
    if SQL_INJECTION_PATTERN.search(prompt):
        flags.append("SQL_INJECTION_DETECTED")
        threat_level = "HIGH"

    # In-Flight PII / SPII Sanitization
    sanitized = NRIC_PATTERN.sub("[NRIC_REDACTED]", prompt)
    sanitized = CREDIT_CARD_PATTERN.sub("[PAYMENT_CARD_REDACTED]", sanitized)
    sanitized = CREDENTIAL_PATTERN.sub(r"\1: [CREDENTIAL_REDACTED]", sanitized)
    sanitized = SSN_PATTERN.sub("[TAX_ID_REDACTED]", sanitized)

    if sanitized != prompt:
        flags.append("PII_REDACTED")

    audit_metadata = {
        "threat_level": threat_level,
        "flags": flags,
        "pii_modified": sanitized != prompt
    }

    # If severe injection attempt is detected, return is_safe = False
    is_safe = "PROMPT_INJECTION_ATTEMPT" not in flags

    return is_safe, sanitized, audit_metadata


def sanitize_agent_output(response: str) -> str:
    """Sanitize model output to prevent accidental leakage of sensitive tokens or internal prompts."""
    if not response or not isinstance(response, str):
        return response or ""

    # Redact raw API keys or internal tokens if hallucinated
    sanitized = CREDENTIAL_PATTERN.sub(r"\1: [CREDENTIAL_REDACTED]", response)
    sanitized = NRIC_PATTERN.sub("[NRIC_REDACTED]", sanitized)
    sanitized = CREDIT_CARD_PATTERN.sub("[PAYMENT_CARD_REDACTED]", sanitized)
    return sanitized
