"""WorkWeek (HCM) Mock Tools for reading/writing employee profiles and leave requests."""
import json
from datetime import datetime

# In-memory mock database
MOCK_WORKWEEK_DB = {
    "emp_001": {
        "employee_id": "emp_001",
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "department": "Engineering",
        "role": "Software Engineer",
        "manager": "emp_002",
        "hire_date": "2022-01-15",
        "home_address": "123 Tech Lane, San Francisco, CA",
        "phone_number": "555-0100",
        "leave_balances": {
            "Vacation": {"accrued": 20, "used": 5, "remaining": 15},
            "Sick": {"accrued": 10, "used": 2, "remaining": 8}
        }
    }
}

def retrieve_employee_profile(employee_id: str) -> str:
    """Retrieve core work and contact metadata for an employee.
    
    Args:
        employee_id: The ID of the employee to look up (e.g., "emp_001")
    """
    if employee_id not in MOCK_WORKWEEK_DB:
        return json.dumps({"error": f"Employee {employee_id} not found."})
    
    profile = MOCK_WORKWEEK_DB[employee_id]
    return json.dumps({
        k: profile[k] for k in profile if k != "leave_balances"
    })

def update_contact_information(employee_id: str, address: str = None, phone_number: str = None) -> str:
    """Update the employee's personal home address and phone number.
    
    Args:
        employee_id: The ID of the employee
        address: New home address
        phone_number: New phone number
    """
    if employee_id not in MOCK_WORKWEEK_DB:
        return json.dumps({"error": f"Employee {employee_id} not found."})
    
    if address:
        MOCK_WORKWEEK_DB[employee_id]["home_address"] = address
    if phone_number:
        MOCK_WORKWEEK_DB[employee_id]["phone_number"] = phone_number
        
    return json.dumps({"status": "Success", "message": "Contact info updated successfully."})

def query_time_off_balances(employee_id: str) -> str:
    """Check accrued, used, and remaining balances for Vacation and Sick leave.
    
    Args:
        employee_id: The ID of the employee
    """
    if employee_id not in MOCK_WORKWEEK_DB:
        return json.dumps({"error": f"Employee {employee_id} not found."})
    
    return json.dumps(MOCK_WORKWEEK_DB[employee_id]["leave_balances"])

def submit_leave_request(employee_id: str, start_date: str, end_date: str, leave_type: str, work_days: int) -> str:
    """Request time off.
    
    Args:
        employee_id: The ID of the employee
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        leave_type: 'Vacation' or 'Sick'
        work_days: Number of days being requested
    """
    if employee_id not in MOCK_WORKWEEK_DB:
        return json.dumps({"error": f"Employee {employee_id} not found."})
        
    balances = MOCK_WORKWEEK_DB[employee_id]["leave_balances"]
    if leave_type not in balances:
        return json.dumps({"error": f"Invalid leave type: {leave_type}"})
        
    if balances[leave_type]["remaining"] < work_days:
        return json.dumps({"error": f"Insufficient {leave_type} balance. Requested: {work_days}, Remaining: {balances[leave_type]['remaining']}"})
        
    # Validation logic - Chronological
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        if start > end:
            return json.dumps({"error": "Start date cannot be after end date."})
    except ValueError:
        return json.dumps({"error": "Invalid date format. Use YYYY-MM-DD."})
        
    # Deduct balances
    balances[leave_type]["remaining"] -= work_days
    balances[leave_type]["used"] += work_days
    
    return json.dumps({
        "status": "Success", 
        "message": f"Leave requested successfully. Remaining {leave_type} balance: {balances[leave_type]['remaining']}"
    })
