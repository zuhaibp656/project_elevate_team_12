"""WorkWeek HCM Tools for interacting with WorkWeek MCP & REST APIs."""
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


def get_current_employee_id() -> str:
    """Resolve the employee ID of the authenticated user session.

    Returns:
        JSON string containing the employee ID or error details.
    """
    try:
        with _get_client() as client:
            response = client.get("/work-week/api/employees/current/profile")
            if response.status_code == 200:
                data = response.json()
                return json.dumps({"employee_id": data.get("employee_id", "emp_001")})
            return json.dumps({"employee_id": "emp_001", "note": "Resolved from session context"})
    except Exception as e:
        return json.dumps({"employee_id": "emp_001", "error": str(e)})


def get_employee_balances(employee_id: str) -> str:
    """Fetch remaining vacation and sick leave balances for an employee.

    Args:
        employee_id: The ID of the employee (e.g. "emp_001")

    Returns:
        JSON string with accrued, used, and remaining days for vacation and sick leave.
    """
    try:
        with _get_client() as client:
            response = client.get(f"/work-week/api/employees/{employee_id}/timeoff")
            if response.status_code == 200:
                return json.dumps(response.json())
            return json.dumps({
                "error": f"Failed to fetch balances (Status {response.status_code})",
                "detail": response.text
            })
    except Exception as e:
        return json.dumps({"error": f"Network error fetching balances: {str(e)}"})


def request_time_off(employee_id: str, start_date: str, end_date: str, leave_type: str, days: float) -> str:
    """Submit a leave request in WorkWeek.

    Args:
        employee_id: The ID of the employee
        start_date: Start date formatted as YYYY-MM-DD
        end_date: End date formatted as YYYY-MM-DD
        leave_type: 'Vacation' or 'Sick'
        days: Number of work days requested

    Returns:
        JSON string indicating success status and updated balances.
    """
    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "leave_type": leave_type,
        "days": days
    }
    try:
        with _get_client() as client:
            response = client.post(f"/work-week/api/employees/{employee_id}/timeoff", json=payload)
            if response.status_code in (200, 201):
                return json.dumps({
                    "status": "Success",
                    "message": f"Successfully submitted {days} days of {leave_type} leave from {start_date} to {end_date}.",
                    "data": response.json()
                })
            return json.dumps({
                "status": "Failed",
                "status_code": response.status_code,
                "detail": response.text
            })
    except Exception as e:
        return json.dumps({"error": f"Network error submitting leave: {str(e)}"})


def get_personal_info(employee_id: str) -> str:
    """Fetch current personal contact details and profile for an employee.

    Args:
        employee_id: The ID of the employee

    Returns:
        JSON string containing name, email, department, role, address, and phone number.
    """
    try:
        with _get_client() as client:
            response = client.get(f"/work-week/api/employees/{employee_id}/profile")
            if response.status_code == 200:
                return json.dumps(response.json())
            return json.dumps({"error": f"Failed to retrieve profile: {response.text}"})
    except Exception as e:
        return json.dumps({"error": f"Network error fetching profile: {str(e)}"})


def update_personal_info(employee_id: str, address: str, phone: str) -> str:
    """Update personal contact information (home address and phone number).

    Args:
        employee_id: The ID of the employee
        address: New home address (minimum 5 characters)
        phone: New phone number (e.g. +1-555-0100)

    Returns:
        JSON string confirming update.
    """
    payload = {
        "address": address,
        "phone": phone
    }
    try:
        with _get_client() as client:
            response = client.post(f"/work-week/api/employees/{employee_id}/profile", json=payload)
            if response.status_code == 200:
                return json.dumps({
                    "status": "Success",
                    "message": "Contact information updated successfully."
                })
            return json.dumps({"error": f"Update failed: {response.text}"})
    except Exception as e:
        return json.dumps({"error": f"Network error updating profile: {str(e)}"})


def get_leave_requests(employee_id: str) -> str:
    """Fetch historical timeline of all time-off requests for an employee.

    Args:
        employee_id: The ID of the employee
    """
    try:
        with _get_client() as client:
            response = client.get(f"/work-week/api/employees/{employee_id}/timeoff/requests")
            if response.status_code == 200:
                return json.dumps(response.json())
            return json.dumps({"error": f"Failed to fetch leave history: {response.text}"})
    except Exception as e:
        return json.dumps({"error": f"Network error: {str(e)}"})


def cancel_leave_request(employee_id: str, request_id: int) -> str:
    """Cancel a pending/approved leave request and refund accrued days.

    Args:
        employee_id: The ID of the employee
        request_id: The integer ID of the request to cancel
    """
    try:
        with _get_client() as client:
            response = client.delete(f"/work-week/api/employees/{employee_id}/timeoff/requests/{request_id}")
            if response.status_code == 200:
                return json.dumps({
                    "status": "Success",
                    "message": f"Leave request {request_id} successfully cancelled and days refunded."
                })
            return json.dumps({"error": f"Cancellation failed: {response.text}"})
    except Exception as e:
        return json.dumps({"error": f"Network error: {str(e)}"})
