"""ServiceImmediately ITSM Tools communicating directly via FastMCP JSON-RPC."""
import json
import httpx
from agents import config

_current_emp_id = "EMP-380"


def _call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call a tool on the ServiceImmediately FastMCP server."""
    headers = {
        "X-MCP-Token": config.MCP_TOKEN,
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json"
    }
    url = f"{config.MOCK_SAAS_BASE_URL.rstrip('/')}/service-immediately/mcp/"

    # Auto-replace placeholder employee IDs with authenticated EMP-380 if needed
    for key in ("employee_id", "requested_by", "author"):
        if key in arguments and (not arguments[key] or str(arguments[key]).lower() in ("emp_001", "me", "current", "self", "learner")):
            arguments[key] = _current_emp_id

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
        return json.dumps({"error": f"Network error calling ServiceImmediately MCP: {str(e)}"})


def list_tickets(employee_id: str = "EMP-380") -> str:
    """List all ServiceImmediately incident tickets requested by an employee.

    Args:
        employee_id: The employee ID (defaults to EMP-380)

    Returns:
        JSON string or list of tickets with ID, category, status, and description.
    """
    return _call_mcp_tool("list_tickets", {"employee_id": employee_id or _current_emp_id})


def get_ticket_details(ticket_id: str) -> str:
    """Retrieve details for a specific incident ticket.

    Args:
        ticket_id: The ID of the ticket (e.g. "INC0002551")
    """
    # Tickets are listed with details from list_tickets
    res = _call_mcp_tool("list_tickets", {"employee_id": _current_emp_id})
    return res


def create_ticket(
    category: str,
    short_description: str,
    priority: str,
    requested_by: str = "EMP-380",
    assignment_group: str = "Service Desk"
) -> str:
    """Submit a new ServiceImmediately incident ticket.

    Args:
        category: Ticket category (e.g. "Hardware", "Software", "Access", "Facilities", "Inquiry / Help")
        short_description: Brief description of the issue or request
        priority: Priority level ('1 - Critical', '2 - High', '3 - Moderate', '4 - Low')
        requested_by: Employee ID opening the request (defaults to EMP-380)
        assignment_group: Group assigned to handle ticket (defaults to 'Service Desk')

    Returns:
        String containing the created ticket details and Ticket ID.
    """
    return _call_mcp_tool("create_ticket", {
        "requested_by": requested_by or _current_emp_id,
        "category": category,
        "short_description": short_description,
        "priority": priority,
        "assignment_group": assignment_group
    })


def add_ticket_comment(ticket_id: str, comment: str, author: str = "EMP-380") -> str:
    """Append a timeline comment to the ticket's activity log.

    Args:
        ticket_id: The ID of the ticket (e.g. "INC0002551")
        comment: Text note to append
        author: Name or ID of the author (defaults to EMP-380)
    """
    return _call_mcp_tool("add_ticket_comment", {
        "ticket_id": ticket_id,
        "author": author or _current_emp_id,
        "comment": comment
    })


def update_ticket_status(ticket_id: str, status: str, resolution_notes: str = "", updated_by: str = "System") -> str:
    """Drive the ticket status state machine (e.g. 'In Progress', 'Resolved', 'Closed').

    Args:
        ticket_id: The ID of the ticket
        status: Target state ('In Progress', 'Resolved', 'Closed')
        resolution_notes: Optional resolution summary
        updated_by: Entity performing update
    """
    return _call_mcp_tool("update_ticket_status", {
        "ticket_id": ticket_id,
        "status": status,
        "resolution_notes": resolution_notes,
        "updated_by": updated_by
    })
