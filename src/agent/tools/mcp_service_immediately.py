"""ServiceImmediately (ITSM) Mock Tools for querying, creating, and updating tickets."""
import json
import uuid

# In-memory mock database for tickets
MOCK_ITSM_DB = {
    "INC123456": {
        "ticket_id": "INC123456",
        "requestor": "emp_001",
        "category": "Hardware",
        "short_description": "VPN connection drops frequently",
        "priority": "3 - Moderate",
        "status": "In Progress",
        "assignee": "helpdesk_01",
        "comments": [
            {"user": "emp_001", "comment": "My VPN drops every 10 minutes."},
            {"user": "helpdesk_01", "comment": "We are investigating the VPN gateway."}
        ]
    }
}

VALID_STATUS_TRANSITIONS = {
    "New": ["In Progress", "Closed", "Resolved"],
    "In Progress": ["On Hold", "Resolved", "Closed"],
    "On Hold": ["In Progress", "Resolved", "Closed"],
    "Resolved": ["Closed"],
    "Closed": []
}

def query_ticket_details(ticket_id: str) -> str:
    """Retrieve current status, category, short description, priority, assignee, and comments for a ticket.
    
    Args:
        ticket_id: ID of the ticket (e.g., "INC123456")
    """
    if ticket_id not in MOCK_ITSM_DB:
        return json.dumps({"error": f"Ticket {ticket_id} not found."})
    return json.dumps(MOCK_ITSM_DB[ticket_id])

def create_incident_ticket(requestor_id: str, category: str, short_description: str, priority: str) -> str:
    """Open a new support ticket.
    
    Args:
        requestor_id: Employee ID
        category: Ticket category (e.g., 'Hardware', 'Software', 'Access')
        short_description: Brief issue description
        priority: '1 - Critical', '2 - High', '3 - Moderate', '4 - Low'
    """
    # Priority Verification
    if priority not in ['1 - Critical', '2 - High', '3 - Moderate', '4 - Low']:
        return json.dumps({"error": "Invalid priority level."})
    
    # Generate new ID
    new_id = f"INC{str(uuid.uuid4().int)[:6]}"
    
    ticket = {
        "ticket_id": new_id,
        "requestor": requestor_id,
        "category": category,
        "short_description": short_description,
        "priority": priority,
        "status": "New",
        "assignee": "Unassigned",
        "comments": []
    }
    
    MOCK_ITSM_DB[new_id] = ticket
    return json.dumps({"status": "Success", "message": f"Ticket {new_id} created successfully.", "ticket_id": new_id})

def post_ticket_comment(ticket_id: str, user_id: str, comment: str) -> str:
    """Append a comment to a ticket.
    
    Args:
        ticket_id: ID of the ticket
        user_id: User posting the comment
        comment: The comment text
    """
    if ticket_id not in MOCK_ITSM_DB:
        return json.dumps({"error": f"Ticket {ticket_id} not found."})
    
    MOCK_ITSM_DB[ticket_id]["comments"].append({"user": user_id, "comment": comment})
    return json.dumps({"status": "Success", "message": "Comment posted successfully."})

def update_ticket_status(ticket_id: str, new_status: str, resolution_notes: str = None) -> str:
    """Update ticket status, enforcing logical transitions.
    
    Args:
        ticket_id: ID of the ticket
        new_status: New status ('In Progress', 'Resolved', 'Closed', etc.)
        resolution_notes: Optional resolution note.
    """
    if ticket_id not in MOCK_ITSM_DB:
        return json.dumps({"error": f"Ticket {ticket_id} not found."})
        
    current_status = MOCK_ITSM_DB[ticket_id]["status"]
    
    # Transition constraints
    allowed_next = VALID_STATUS_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        return json.dumps({"error": f"Invalid transition from {current_status} to {new_status}."})
        
    MOCK_ITSM_DB[ticket_id]["status"] = new_status
    if resolution_notes:
        MOCK_ITSM_DB[ticket_id]["comments"].append({"user": "system", "comment": f"Resolution: {resolution_notes}"})
        
    return json.dumps({"status": "Success", "message": f"Ticket status updated to {new_status}."})
