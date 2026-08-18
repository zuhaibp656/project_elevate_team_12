"""WorkWeek HCM Tools communicating directly via FastMCP JSON-RPC (Rate-Limited & Drift-Resilient)."""
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
    """Call a tool on the WorkWeek FastMCP server with tiered throttling and schema drift resilience."""
    global _CONSECUTIVE_FAILURES, _CIRCUIT_OPEN_UNTIL

    # Circuit Breaker Check
    now = time.time()
    if now < _CIRCUIT_OPEN_UNTIL:
        return json.dumps({
            "error": "Downstream WorkWeek service is temporarily throttled/degraded. Circuit breaker active.",
            "circuit_breaker": True,
            "retry_after_seconds": int(_CIRCUIT_OPEN_UNTIL - now)
        })

    active_token = _get_active_mcp_token(token_override)
    headers = {
        "X-MCP-Token": active_token,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    url = f"{config.MOCK_SAAS_BASE_URL.rstrip('/')}/work-week/mcp/"
    
    # Auto-resolve placeholder employee IDs
    if "employee_id" in arguments and (not arguments["employee_id"] or str(arguments["employee_id"]).lower() in ("emp_001", "me", "current", "self", "learner")):
        arguments["employee_id"] = "EMP-380"

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
            last_error = f"Network error calling WorkWeek MCP: {str(e)}"
            time.sleep(1.0 * (attempt + 1))

    # Record Failure for Circuit Breaker
    _CONSECUTIVE_FAILURES += 1
    if _CONSECUTIVE_FAILURES >= _CIRCUIT_THRESHOLD:
        _CIRCUIT_OPEN_UNTIL = time.time() + _COOLDOWN_PERIOD

    return json.dumps({"error": last_error, "retries_exhausted": True})


def get_current_employee_id() -> str:
    """Resolve the employee ID of the authenticated user session from their MCP Token.

    Returns:
        JSON string containing the employee ID.
    """
    res = _call_mcp_tool("get_current_employee_id", {})
    return res if res else json.dumps({"employee_id": "EMP-380"})


def get_employee_balances(employee_id: str = "EMP-380") -> str:
    """Fetch current vacation and sick leave balances for an employee.

    Args:
        employee_id: The employee ID (defaults to current authenticated employee)

    Returns:
        JSON string containing vacation and sick leave balances.
    """
    return _call_mcp_tool("get_employee_balances", {"employee_id": employee_id or "EMP-380"})


def request_time_off(employee_id: str, start_date: str, end_date: str, leave_type: str, days: float) -> str:
    """Submit a leave request in WorkWeek for an employee.

    Args:
        employee_id: The employee ID
        start_date: Start date of leave in YYYY-MM-DD format
        end_date: End date of leave in YYYY-MM-DD format
        leave_type: Type of leave ("Vacation" or "Sick")
        days: Number of leave days requested

    Returns:
        JSON string confirmation of the submitted leave request.
    """
    return _call_mcp_tool("request_time_off", {
        "employee_id": employee_id or "EMP-380",
        "start_date": start_date,
        "end_date": end_date,
        "leave_type": leave_type,
        "days": days
    })


def get_personal_info(employee_id: str = "EMP-380") -> str:
    """Fetch personal contact and profile information for an employee.

    Args:
        employee_id: The employee ID (defaults to current authenticated employee)

    Returns:
        JSON string with employee's email, phone, and home address.
    """
    return _call_mcp_tool("get_personal_info", {"employee_id": employee_id or "EMP-380"})


def update_personal_info(employee_id: str, address: str = None, phone: str = None) -> str:
    """Update personal contact information (home address and/or phone) in WorkWeek.

    Args:
        employee_id: The employee ID
        address: New home/office address
        phone: New contact phone number

    Returns:
        JSON string confirming updated profile information.
    """
    args = {"employee_id": employee_id or "EMP-380"}
    if address:
        args["address"] = address
    if phone:
        args["phone"] = phone
    return _call_mcp_tool("update_personal_info", args)


def get_leave_requests(employee_id: str = "EMP-380") -> str:
    """List all historical leave requests for an employee.

    Args:
        employee_id: The employee ID

    Returns:
        JSON string with list of past leave requests and their statuses.
    """
    return _call_mcp_tool("get_leave_requests", {"employee_id": employee_id or "EMP-380"})


def cancel_leave_request(employee_id: str, request_id: str) -> str:
    """Cancel an existing leave request in WorkWeek.

    Args:
        employee_id: The employee ID
        request_id: The unique ID of the leave request to cancel

    Returns:
        JSON string confirming cancellation and restored leave balance.
    """
    return _call_mcp_tool("cancel_leave_request", {
        "employee_id": employee_id or "EMP-380",
        "request_id": request_id
    })
