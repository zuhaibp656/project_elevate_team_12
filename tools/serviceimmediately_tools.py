"""ServiceImmediately ITSM Tools communicating directly via FastMCP JSON-RPC (Rate-Limited & Drift-Resilient)."""
import os
import json
import time
import httpx
from agents import config

# Circuit Breaker & Throttling Configuration
_CONSECUTIVE_FAILURES = 0
_CIRCUIT_OPEN_UNTIL = 0.0
_MAX_RETRIES = 2
_CIRCUIT_THRESHOLD = 5
_COOLDOWN_PERIOD = 30.0  # seconds


def _get_active_mcp_token(token_override: str = None) -> str:
    """Get the active MCP token for the current user/session."""
    return token_override or os.getenv("MCP_TOKEN", config.MCP_TOKEN)


def _call_mcp_tool(tool_name: str, arguments: dict, token_override: str = None) -> str:
    """Call a tool on the ServiceImmediately FastMCP server with tiered throttling and schema drift resilience."""
    global _CONSECUTIVE_FAILURES, _CIRCUIT_OPEN_UNTIL

    # Circuit Breaker Check
    now = time.time()
    if now < _CIRCUIT_OPEN_UNTIL:
        return json.dumps({
            "error": "Downstream ServiceImmediately ITSM service is temporarily throttled/degraded. Circuit breaker active.",
            "circuit_breaker": True,
            "retry_after_seconds": int(_CIRCUIT_OPEN_UNTIL - now)
        })

    active_token = _get_active_mcp_token(token_override)
    headers = {
        "X-MCP-Token": active_token,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    url = f"{config.MOCK_SAAS_BASE_URL.rstrip('/')}/service-immediately/mcp/"

    # Auto-resolve placeholder employee IDs
    for key in ("employee_id", "requested_by", "author", "updated_by"):
        if key in arguments and (not arguments[key] or str(arguments[key]).lower() in ("emp_001", "me", "current", "self", "learner")):
            arguments[key] = "EMP-380"

    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 100000,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    last_error = ""
    for attempt in range(_MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, headers=headers, json=payload)
                
                # Handle Rate Limiting (HTTP 429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "2"))
                    time.sleep(min(retry_after, 3))
                    continue

                if response.status_code == 200:
                    _CONSECUTIVE_FAILURES = 0  # Reset circuit breaker
                    data = response.json()
                    if "error" in data:
                        return json.dumps({"error": data["error"]})
                    result = data.get("result", {})
                    content = result.get("content", [])
                    if content and isinstance(content, list) and len(content) > 0:
                        return content[0].get("text", json.dumps(result))
                    return json.dumps(result)
                
                last_error = f"MCP returned status {response.status_code}: {response.text}"
                if response.status_code >= 500:
                    time.sleep(1.0 * (attempt + 1))
        except Exception as e:
            last_error = f"Network error calling ServiceImmediately MCP: {str(e)}"
            time.sleep(1.0 * (attempt + 1))

    # Record Failure for Circuit Breaker
    _CONSECUTIVE_FAILURES += 1
    if _CONSECUTIVE_FAILURES >= _CIRCUIT_THRESHOLD:
        _CIRCUIT_OPEN_UNTIL = time.time() + _COOLDOWN_PERIOD

    return json.dumps({"error": last_error, "retries_exhausted": True})


def list_tickets(employee_id: str = "EMP-380") -> str:
    """List all ServiceImmediately incident tickets requested by an employee.

    Args:
        employee_id: The employee ID (defaults to current authenticated employee)

    Returns:
        JSON string or list of tickets with ID, category, status, and description.
    """
    return _call_mcp_tool("list_tickets", {"employee_id": employee_id or "EMP-380"})


def get_ticket_details(ticket_id: str) -> str:
    """Get complete details for a specific ServiceImmediately incident ticket.

    Args:
        ticket_id: The ticket ID (e.g., "INC0002551")

    Returns:
        JSON string with ticket attributes, comments, and current status.
    """
    raw = _call_mcp_tool("list_tickets", {"employee_id": "EMP-380"})
    try:
        tickets = json.loads(raw)
        if isinstance(tickets, list):
            for t in tickets:
                if t.get("ticket_id") == ticket_id or t.get("id") == ticket_id:
                    return json.dumps(t)
    except Exception:
        pass
    return raw


def create_ticket(
    requested_by: str,
    category: str,
    short_description: str,
    priority: str = "3 - Moderate",
    assignment_group: str = "Service Desk"
) -> str:
    """Create a new support incident ticket in ServiceImmediately.

    Args:
        requested_by: Employee ID of the requester
        category: Ticket category ("Hardware", "Software", "Access", "Facilities", "Inquiry / Help")
        short_description: Summary describing the request or issue
        priority: Priority tier ("1 - Critical", "2 - High", "3 - Moderate", "4 - Low")
        assignment_group: Support group handling the ticket ("Service Desk", "HR Support", "Facilities")

    Returns:
        JSON string confirming ticket creation with generated ticket ID (e.g. INC0002594).
    """
    return _call_mcp_tool("create_ticket", {
        "requested_by": requested_by or "EMP-380",
        "category": category,
        "short_description": short_description,
        "priority": priority,
        "assignment_group": assignment_group
    })


def add_ticket_comment(ticket_id: str, author: str, comment: str) -> str:
    """Add a work note or comment update to an existing ticket.

    Args:
        ticket_id: The ticket ID (e.g., "INC0002551")
        author: The employee ID adding the comment
        comment: The message or note text to append

    Returns:
        JSON string confirming comment was appended.
    """
    return _call_mcp_tool("add_ticket_comment", {
        "ticket_id": ticket_id,
        "author": author or "EMP-380",
        "comment": comment
    })


def update_ticket_status(ticket_id: str, status: str, resolution_notes: str = "", updated_by: str = "EMP-380") -> str:
    """Update the lifecycle status of a support ticket.

    Args:
        ticket_id: The ticket ID (e.g., "INC0002551")
        status: Target state ("New", "In Progress", "Resolved", "Closed")
        resolution_notes: Reason or resolution notes (required for Resolved/Closed)
        updated_by: Employee ID making the update

    Returns:
        JSON string confirming status transition.
    """
    return _call_mcp_tool("update_ticket_status", {
        "ticket_id": ticket_id,
        "status": status,
        "resolution_notes": resolution_notes or "Resolved via self-service orchestrator.",
        "updated_by": updated_by or "EMP-380"
    })


def escalate_to_human_hr(requested_by: str = "EMP-380", reason: str = "", conversation_summary: str = "") -> str:
    """Escalate an unresolved transaction or query to a human HR specialist.

    Args:
        requested_by: Employee ID of the requester
        reason: Cause for escalation (e.g., peak timeout, policy ambiguity, transaction exception)
        conversation_summary: Summary of user request and failed actions

    Returns:
        JSON string with created Tier-2 HR Escalation Ticket ID.
    """
    desc = f"[TIER-2 HR ESCALATION] {reason}. Context: {conversation_summary or 'Automated fallback triggered.'}"
    return create_ticket(
        requested_by=requested_by or "EMP-380",
        category="Inquiry / Help",
        short_description=desc[:160],
        priority="2 - High",
        assignment_group="HR Support"
    )
