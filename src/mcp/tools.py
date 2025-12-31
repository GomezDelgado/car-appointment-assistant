"""MCP-style tools for the car appointment assistant."""

from typing import Optional
from langchain_core.tools import tool

from src.data.mock_data import (
    search_dealerships as _search_dealerships,
    get_availability as _get_availability,
    book_appointment as _book_appointment,
    get_dealership_by_id,
    Dealership,
    TimeSlot,
)


@tool
def search_dealerships(
    service: Optional[str] = None,
    location: Optional[str] = None,
) -> str:
    """
    Search for car dealerships that offer a specific service.
    
    Args:
        service: The service needed (e.g., "oil change", "brake inspection", "revision")
        location: Optional location filter (e.g., "Madrid", "Getafe")
    
    Returns:
        A formatted string with the list of matching dealerships.
    """
    results = _search_dealerships(location=location, service=service)
    
    if not results:
        return "No dealerships found matching your criteria."
    
    output_lines = [f"Found {len(results)} dealership(s):\n"]
    for dealer in results:
        output_lines.append(f"- {dealer.name} ({dealer.location})")
        output_lines.append(f"  ID: {dealer.id}")
        output_lines.append(f"  Phone: {dealer.phone}")
        output_lines.append(f"  Services: {', '.join(dealer.services)}")
        output_lines.append("")
    
    return "\n".join(output_lines)


@tool
def check_availability(
    dealership_id: str,
    date: Optional[str] = None,
) -> str:
    """
    Check available appointment slots at a dealership.
    
    Args:
        dealership_id: The ID of the dealership (e.g., "dealer_001")
        date: Optional specific date to check (format: YYYY-MM-DD)
    
    Returns:
        A formatted string with available time slots.
    """
    dealer = get_dealership_by_id(dealership_id)
    if not dealer:
        return f"Dealership with ID '{dealership_id}' not found."
    
    slots = _get_availability(dealership_id=dealership_id, date=date)
    
    if not slots:
        return f"No available slots at {dealer.name}" + (f" on {date}" if date else "") + "."
    
    output_lines = [f"Available slots at {dealer.name}:\n"]
    
    # Group by date
    slots_by_date: dict[str, list[str]] = {}
    for slot in slots:
        if slot.date not in slots_by_date:
            slots_by_date[slot.date] = []
        slots_by_date[slot.date].append(slot.time)
    
    for slot_date, times in sorted(slots_by_date.items()):
        output_lines.append(f"  {slot_date}: {', '.join(sorted(times))}")
    
    return "\n".join(output_lines)


@tool
def book_appointment(
    dealership_id: str,
    service: str,
    date: str,
    time: str,
    customer_name: Optional[str] = None,
) -> str:
    """
    Book an appointment at a dealership.
    
    Args:
        dealership_id: The ID of the dealership (e.g., "dealer_001")
        service: The service to book (e.g., "oil_change", "brake_inspection")
        date: The date for the appointment (format: YYYY-MM-DD)
        time: The time for the appointment (format: HH:MM)
        customer_name: Optional name of the customer
    
    Returns:
        Confirmation message with appointment details or error message.
    """
    dealer = get_dealership_by_id(dealership_id)
    if not dealer:
        return f"Dealership with ID '{dealership_id}' not found."
    
    appointment = _book_appointment(
        dealership_id=dealership_id,
        service=service,
        date=date,
        time=time,
        customer_name=customer_name,
    )
    
    if not appointment:
        return f"Sorry, the slot at {time} on {date} is not available at {dealer.name}."
    
    return (
        f"Appointment confirmed!\n"
        f"  Confirmation ID: {appointment.id}\n"
        f"  Dealership: {dealer.name}\n"
        f"  Service: {appointment.service}\n"
        f"  Date: {appointment.date}\n"
        f"  Time: {appointment.time}\n"
        + (f"  Customer: {appointment.customer_name}\n" if appointment.customer_name else "")
    )


# List of all available tools for the agent
TOOLS = [search_dealerships, check_availability, book_appointment]
