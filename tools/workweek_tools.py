"""WorkWeek HCM Tools communicating directly via FastMCP JSON-RPC."""
import json
import httpx
from agents import config

_current_emp_id = "EMP-380"


def _call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call a tool on the WorkWeek FastMCP server."""
    headers = {
        "X-MCP-Token": config.MCP_TOKEN,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    url = f"{config.MOCK_SAAS_BASE_URL.rstrip('/')}/work-week/mcp/"
    
    # Auto-replace placeholder employee IDs with authenticated EMP-380 if needed
    if "employee_id" in arguments and (not arguments["employee_id"] or arguments["employee_id"].lower() in ("emp_001", "me", "current", "self", "learner")):
        arguments["employee_id"] = _current_emp_id

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    return json.dumps({"error": data["error"]})
                result = data.get("result", {})
                content = result.get("content", [])
                if content and isinstance(content, list) and len(content) > 0:
                    return content[0].get("text", json.dumps(result))
                return json.dumps(result)
            return json.dumps({"error": f"MCP returned status {response.status_code}: {response.text}"})
    except Exception as e:
        return json.dumps({"error": f"Network error calling WorkWeek MCP: {str(e)}"})


def get_current_employee_id() -> str:
    """Resolve the employee ID of the authenticated user session.

    Returns:
        JSON string containing the employee ID.
    """
    res = _call_mcp_tool("get_current_employee_id", {})
    return res if res else json.dumps({"employee_id": _current_emp_id})


def get_employee_balances(employee_id: str = "EMP-380") -> str:
    """Fetch current vacation and sick leave balances for an employee.

    Args:
        employee_id: The ID of the employee (e.g. "EMP-380")

    Returns:
        String with accrued, used, and remaining days for vacation and sick leave.
    """
    return _call_mcp_tool("get_employee_balances", {"employee_id": employee_id or _current_emp_id})


def request_time_off(start_date: str, end_date: str, leave_type: str, days: float, employee_id: str = "EMP-380") -> str:
    """Submit a leave request in WorkWeek.

    Args:
        start_date: Start date formatted as YYYY-MM-DD
        end_date: End date formatted as YYYY-MM-DD
        leave_type: 'Vacation' or 'Sick'
        days: Number of work days requested
        employee_id: The ID of the employee (defaults to authenticated user EMP-380)

    Returns:
        String indicating success status and updated balances.
    """
    return _call_mcp_tool("request_time_off", {
        "employee_id": employee_id or _current_emp_id,
        "start_date": start_date,
        "end_date": end_date,
        "leave_type": leave_type,
        "days": days
    })


def get_personal_info(employee_id: str = "EMP-380") -> str:
    """Fetch current personal contact details and address for an employee.

    Args:
        employee_id: The ID of the employee (defaults to EMP-380)

    Returns:
        String containing employee personal contact details.
    """
    return _call_mcp_tool("get_personal_info", {"employee_id": employee_id or _current_emp_id})


def update_personal_info(address: str, phone: str, employee_id: str = "EMP-380") -> str:
    """Update personal contact information (home address and phone number).

    Args:
        address: New home address (minimum 5 characters)
        phone: New phone number (e.g. +65-6521-0000)
        employee_id: The ID of the employee (defaults to EMP-380)

    Returns:
        String confirming update.
    """
    return _call_mcp_tool("update_personal_info", {
        "employee_id": employee_id or _current_emp_id,
        "address": address,
        "phone": phone
    })


def get_leave_requests(employee_id: str = "EMP-380") -> str:
    """Fetch historical timeline of all time-off requests for an employee.

    Args:
        employee_id: The ID of the employee (defaults to EMP-380)
    """
    return _call_mcp_tool("get_leave_requests", {"employee_id": employee_id or _current_emp_id})


def cancel_leave_request(request_id: int, employee_id: str = "EMP-380") -> str:
    """Cancel a pending/approved leave request and refund accrued days.

    Args:
        request_id: The integer ID of the request to cancel
        employee_id: The ID of the employee (defaults to EMP-380)
    """
    return _call_mcp_tool("cancel_leave_request", {
        "employee_id": employee_id or _current_emp_id,
        "request_id": request_id
    })
