"""ServiceImmediately ITSM Tools for interacting with ITSM MCP & REST APIs."""
import json
import httpx
from agents import config


def _get_client() -> httpx.Client:
    headers = {
        "X-MCP-Token": config.MCP_TOKEN,
        "Content-Type": "application/json"
    }
    return httpx.Client(
        base_url=config.MOCK_SAAS_BASE_URL.rstrip("/"),
        headers=headers,
        timeout=15.0
    )


def list_tickets(employee_id: str = None) -> str:
    """List support incident tickets requested by the employee.

    Args:
        employee_id: Optional employee ID to filter tickets.

    Returns:
        JSON string containing list of tickets with ID, category, status, and description.
    """
    params = {}
    if employee_id:
        params["requested_by"] = employee_id

    try:
        with _get_client() as client:
            response = client.get("/service-immediately/api/tickets", params=params)
            if response.status_code == 200:
                return json.dumps(response.json())
            return json.dumps({"error": f"Failed to list tickets: {response.text}"})
    except Exception as e:
        return json.dumps({"error": f"Network error listing tickets: {str(e)}"})


def get_ticket_details(ticket_id: str) -> str:
    """Retrieve full structural details, assignee, status, and comments for a specific incident ticket.

    Args:
        ticket_id: The ID of the ticket (e.g. "INC123456")
    """
    try:
        with _get_client() as client:
            response = client.get(f"/service-immediately/api/tickets/{ticket_id}")
            if response.status_code == 200:
                return json.dumps(response.json())
            return json.dumps({"error": f"Failed to fetch ticket {ticket_id}: {response.text}"})
    except Exception as e:
        return json.dumps({"error": f"Network error: {str(e)}"})


def create_ticket(
    requested_by: str,
    category: str,
    short_description: str,
    priority: str,
    assignment_group: str = "Service Desk"
) -> str:
    """Submit a new ServiceImmediately incident ticket.

    Args:
        requested_by: Employee ID opening the request (e.g. "emp_001")
        category: Ticket category (e.g. "Hardware", "Software", "Access", "Facilities")
        short_description: Brief description of the issue or request
        priority: Priority level ('1 - Critical', '2 - High', '3 - Moderate', '4 - Low')
        assignment_group: Group assigned to handle ticket (defaults to 'Service Desk')

    Returns:
        JSON string containing the created ticket details and Ticket ID.
    """
    payload = {
        "requested_by": requested_by,
        "category": category,
        "short_description": short_description,
        "priority": priority,
        "assignment_group": assignment_group
    }
    try:
        with _get_client() as client:
            response = client.post("/service-immediately/api/tickets", json=payload)
            if response.status_code in (200, 201):
                data = response.json()
                return json.dumps({
                    "status": "Success",
                    "message": f"Support ticket created successfully.",
                    "ticket": data
                })
            return json.dumps({
                "status": "Failed",
                "status_code": response.status_code,
                "detail": response.text
            })
    except Exception as e:
        return json.dumps({"error": f"Network error creating ticket: {str(e)}"})


def add_ticket_comment(ticket_id: str, author: str, comment: str) -> str:
    """Append an update comment to the incident's activity timeline.

    Args:
        ticket_id: The ID of the ticket
        author: Name or ID of the user posting the comment
        comment: Text note to append
    """
    payload = {
        "author": author,
        "comment_text": comment
    }
    try:
        with _get_client() as client:
            response = client.post(f"/service-immediately/api/tickets/{ticket_id}/comments", json=payload)
            if response.status_code in (200, 201):
                return json.dumps({
                    "status": "Success",
                    "message": f"Comment posted to ticket {ticket_id}."
                })
            return json.dumps({"error": f"Failed to post comment: {response.text}"})
    except Exception as e:
        return json.dumps({"error": f"Network error: {str(e)}"})


def update_ticket_status(ticket_id: str, status: str, resolution_notes: str = "", updated_by: str = "System") -> str:
    """Transition the lifecycle state of a ticket (e.g. In Progress, Resolved, Closed).

    Args:
        ticket_id: The ID of the ticket
        status: Target state ('In Progress', 'Resolved', 'Closed')
        resolution_notes: Optional resolution summary
        updated_by: Entity performing update
    """
    payload = {
        "status": status,
        "resolution_notes": resolution_notes,
        "updated_by": updated_by
    }
    try:
        with _get_client() as client:
            response = client.post(f"/service-immediately/api/tickets/{ticket_id}/status", json=payload)
            if response.status_code == 200:
                return json.dumps({
                    "status": "Success",
                    "message": f"Ticket {ticket_id} status updated to {status}."
                })
            return json.dumps({"error": f"Status transition failed: {response.text}"})
    except Exception as e:
        return json.dumps({"error": f"Network error: {str(e)}"})
