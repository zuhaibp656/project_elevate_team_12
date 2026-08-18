"""Persistent Storage Adapter & In-Flight PII Sanitizer (GDPR / PDPA & Cloud SQL Compliant)."""
import os
import re
import sqlite3
import threading
import json
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.getenv("STORAGE_DB_PATH", os.path.join(REPO_ROOT, "hr_agentic_sessions.db"))

_DB_LOCK = threading.Lock()

# Regex Patterns for In-Flight PII / SPII Redaction
NRIC_PATTERN = re.compile(r"\b[STFGM]\d{7}[A-Z]\b", re.IGNORECASE)
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
CREDENTIAL_PATTERN = re.compile(r"(?i)(password|secret|api[_-]?key)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{8,})['\"]?")


def sanitize_pii(text: str) -> str:
    """Sanitize in-flight SPII and PII (Singapore NRIC, credit cards, credentials) before LLM or DB storage."""
    if not text or not isinstance(text, str):
        return text
    sanitized = NRIC_PATTERN.sub("[NRIC_REDACTED]", text)
    sanitized = CREDIT_CARD_PATTERN.sub("[PAYMENT_CARD_REDACTED]", sanitized)
    sanitized = CREDENTIAL_PATTERN.sub(r"\1: [CREDENTIAL_REDACTED]", sanitized)
    return sanitized


def init_db():
    """Initialize relational database tables for session persistence and audit logging."""
    with _DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT,
            full_name TEXT,
            department TEXT,
            country_code TEXT DEFAULT 'SG',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            channel TEXT DEFAULT 'web_aura',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            correlation_id TEXT,
            sender_role TEXT,
            content TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_executions (
            execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            correlation_id TEXT,
            agent_name TEXT,
            tool_name TEXT,
            parameters TEXT,
            response_payload TEXT,
            status TEXT,
            latency_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalation_tickets (
            ticket_id TEXT PRIMARY KEY,
            session_id TEXT,
            user_id TEXT,
            correlation_id TEXT,
            reason TEXT,
            priority TEXT DEFAULT '2 - High',
            status TEXT DEFAULT 'New',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        conn.commit()
        conn.close()


def record_session(session_id: str, user_id: str, title: str):
    """Upsert a chat session record."""
    with _DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO chat_sessions (session_id, user_id, title)
            VALUES (?, ?, ?)
        """, (session_id, user_id, sanitize_pii(title)))
        conn.commit()
        conn.close()


def record_message(session_id: str, correlation_id: str, sender_role: str, content: str, input_tokens: int = 0, output_tokens: int = 0):
    """Record an inbound or outbound message with in-flight PII sanitization."""
    sanitized = sanitize_pii(content)
    with _DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO session_messages (session_id, correlation_id, sender_role, content, input_tokens, output_tokens)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, correlation_id or "local-trace", sender_role, sanitized, input_tokens, output_tokens))
        conn.commit()
        conn.close()


def record_tool_execution(session_id: str, correlation_id: str, agent_name: str, tool_name: str, parameters: dict, response: any, status: str = "SUCCESS", latency_ms: int = 0):
    """Record an audit trail entry for sub-agent tool execution."""
    with _DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tool_executions (session_id, correlation_id, agent_name, tool_name, parameters, response_payload, status, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            correlation_id or "local-trace",
            agent_name,
            tool_name,
            json.dumps(parameters or {}),
            sanitize_pii(str(response)),
            status,
            latency_ms
        ))
        conn.commit()
        conn.close()


def purge_user_data(user_id: str) -> int:
    """Purge all sessions and message transcripts for an employee (GDPR / Singapore PDPA Right to be Forgotten)."""
    with _DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT session_id FROM chat_sessions WHERE user_id = ?", (user_id,))
        sessions = [row[0] for row in cursor.fetchall()]
        
        for sess_id in sessions:
            cursor.execute("DELETE FROM session_messages WHERE session_id = ?", (sess_id,))
            cursor.execute("DELETE FROM tool_executions WHERE session_id = ?", (sess_id,))
            cursor.execute("DELETE FROM escalation_tickets WHERE session_id = ?", (sess_id,))
            
        cursor.execute("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        return len(sessions)


# Initialize DB on module import
init_db()
