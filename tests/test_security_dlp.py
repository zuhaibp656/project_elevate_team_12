"""Automated unit tests for In-Flight PII Sanitization & GDPR Purge Lifecycle."""
from agents.storage import (
    sanitize_pii,
    record_session,
    record_message,
    purge_user_data
)


def test_nric_sanitization():
    """Verify Singapore NRIC/FIN patterns are masked in-flight."""
    raw = "My NRIC number is S1234567A and my passport is valid."
    sanitized = sanitize_pii(raw)
    assert "S1234567A" not in sanitized
    assert "[NRIC_REDACTED]" in sanitized


def test_credit_card_sanitization():
    """Verify payment card numbers are masked."""
    raw = "Please charge my corporate card 4111 2222 3333 4444 for the taxi."
    sanitized = sanitize_pii(raw)
    assert "4111 2222 3333 4444" not in sanitized
    assert "[PAYMENT_CARD_REDACTED]" in sanitized


def test_credential_sanitization():
    """Verify passwords and API keys are redacted."""
    raw = "My temporary password: SecretPassword123! to login."
    sanitized = sanitize_pii(raw)
    assert "SecretPassword123!" not in sanitized
    assert "[CREDENTIAL_REDACTED]" in sanitized


def test_gdpr_right_to_be_forgotten_purge():
    """Verify purge_user_data deletes user sessions and messages completely."""
    test_user = "EMP-TEST-99"
    test_session = "sess-test-99"
    
    record_session(test_session, test_user, "Test Inquiry")
    record_message(test_session, "corr-1", "user", "Hello World")
    
    purged_count = purge_user_data(test_user)
    assert purged_count >= 1
