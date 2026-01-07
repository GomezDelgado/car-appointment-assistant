"""MCP-style tools for the car appointment assistant."""

from typing import Optional
from langchain_core.tools import tool

from src.data.mock_data import (
    search_dealerships as _search_dealerships,
    get_availability as _get_availability,
    book_appointment as _book_appointment,
    get_bookings as _get_bookings,
    get_booking_by_id as _get_booking_by_id,
    cancel_booking as _cancel_booking,
    modify_booking as _modify_booking,
    resolve_dealership,
    get_dealership_by_id,
    Dealership,
    TimeSlot,
)


@tool
def get_dealership_info(dealership_name: str) -> str:
    """
    Get detailed contact information about a specific dealership.
    Use this when user asks for contact info, phone, address, or details about a dealership.

    Args:
        dealership_name: The name of the dealership (e.g., "Downtown Auto Service")

    Returns:
        Detailed information about the dealership.
    """
    dealer = resolve_dealership(dealership_name)
    if not dealer:
        return f"Dealership '{dealership_name}' not found."

    return (
        f"{dealer.name}\n"
        f"  Address: {dealer.address}\n"
        f"  Phone: {dealer.phone}\n"
        f"  Services: {', '.join(dealer.services)}\n"
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
        output_lines.append(f"- **{dealer.name}** ({dealer.location})")
        output_lines.append(f"  Address: {dealer.address}")
        output_lines.append(f"  Phone: {dealer.phone}")
        output_lines.append(f"  Services: {', '.join(dealer.services)}")
        output_lines.append("")

    return "\n".join(output_lines)


@tool
def check_availability(
    dealership_name: str,
    date: Optional[str] = None,
) -> str:
    """
    Check available appointment slots at a dealership.

    Args:
        dealership_name: The name of the dealership (e.g., "Downtown Auto Service")
        date: Optional specific date to check (format: YYYY-MM-DD). Pass None or omit for all dates.

    Returns:
        A formatted string with available time slots.
    """
    dealer = resolve_dealership(dealership_name)
    if not dealer:
        return f"Dealership '{dealership_name}' not found."

    # Handle null/None date properly
    actual_date = date if date and date != "null" else None
    slots = _get_availability(dealership_id=dealer.id, date=actual_date)

    if not slots:
        return f"No available slots at {dealer.name}" + (f" on {actual_date}" if actual_date else "") + "."
    
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
def compare_availability(location: Optional[str] = None, service: Optional[str] = None) -> str:
    """
    Compare availability across multiple dealerships to find the soonest appointment.
    Use this when user asks "which dealer has soonest availability" or wants to compare dealers.

    Args:
        location: Optional location to filter dealerships (e.g., "Manhattan")
        service: Optional service to filter dealerships (e.g., "brake_inspection", "oil_change")

    Returns:
        Comparison of first available slots at each dealership.
    """
    from src.data.mock_data import DEALERSHIPS, normalize_service

    dealers = DEALERSHIPS
    if location:
        location_lower = location.lower()
        dealers = [d for d in dealers if location_lower in d.location.lower()]

    if service:
        normalized = normalize_service(service) or service
        dealers = [d for d in dealers if normalized in d.services]

    if not dealers:
        filters = []
        if location:
            filters.append(f"in {location}")
        if service:
            filters.append(f"offering {service}")
        return f"No dealerships found {' '.join(filters)}." if filters else "No dealerships found."

    results = []
    for dealer in dealers:
        slots = _get_availability(dealership_id=dealer.id)
        if slots:
            sorted_slots = sorted(slots, key=lambda s: (s.date, s.time))
            first = sorted_slots[0]
            results.append({
                "dealer": dealer,
                "date": first.date,
                "time": first.time,
            })

    if not results:
        return "No availability found at any dealership."

    # Sort by earliest availability
    results.sort(key=lambda r: (r["date"], r["time"]))

    output_lines = ["Soonest availability by dealership:\n"]
    for i, r in enumerate(results):
        marker = " ✓ SOONEST" if i == 0 else ""
        output_lines.append(f"- **{r['dealer'].name}** ({r['dealer'].location}){marker}")
        output_lines.append(f"  First available: {r['date']} at {r['time']}")
        output_lines.append(f"  Address: {r['dealer'].address}")
        output_lines.append(f"  Phone: {r['dealer'].phone}")
        output_lines.append("")

    return "\n".join(output_lines)


@tool
def book_next_available(
    dealership_name: str,
    service: Optional[str] = None,
    customer_name: Optional[str] = None,
) -> str:
    """
    Book the next available appointment slot at a dealership.
    Use this when user wants "the soonest", "earliest", "next available", or "as soon as possible".

    Args:
        dealership_name: The name of the dealership (e.g., "Downtown Auto Service")
        service: The service to book (default: "oil_change")
        customer_name: Optional name of the customer

    Returns:
        Confirmation message with appointment details or error message.
    """
    dealer = resolve_dealership(dealership_name)
    if not dealer:
        return f"Dealership '{dealership_name}' not found."

    service = service or "oil_change"
    slots = _get_availability(dealership_id=dealer.id)

    if not slots:
        return f"No available slots at {dealer.name}."

    # Get the first available slot (sorted by date and time)
    sorted_slots = sorted(slots, key=lambda s: (s.date, s.time))
    first_slot = sorted_slots[0]

    appointment = _book_appointment(
        dealership_id=dealer.id,
        service=service,
        date=first_slot.date,
        time=first_slot.time,
        customer_name=customer_name,
    )

    if not appointment:
        return f"Sorry, could not book the appointment at {dealer.name}."

    return (
        f"✓ Appointment confirmed!\n"
        f"  Confirmation ID: {appointment.id}\n"
        f"  Dealership: **{dealer.name}**\n"
        f"  Address: {dealer.address}\n"
        f"  Phone: {dealer.phone}\n"
        f"  Service: {appointment.service}\n"
        f"  Date: {appointment.date}\n"
        f"  Time: {appointment.time}\n"
        + (f"  Customer: {appointment.customer_name}\n" if appointment.customer_name else "")
    )


@tool
def book_appointment(
    dealership_name: str,
    service: str,
    date: str,
    time: str,
    customer_name: Optional[str] = None,
) -> str:
    """
    Book an appointment at a dealership.

    Args:
        dealership_name: The name of the dealership (e.g., "Downtown Auto Service")
        service: The service to book (e.g., "oil_change", "brake_inspection")
        date: The date for the appointment (format: YYYY-MM-DD)
        time: The time for the appointment (format: HH:MM)
        customer_name: Optional name of the customer

    Returns:
        Confirmation message with appointment details or error message.
    """
    dealer = resolve_dealership(dealership_name)
    if not dealer:
        return f"Dealership '{dealership_name}' not found."

    appointment = _book_appointment(
        dealership_id=dealer.id,
        service=service,
        date=date,
        time=time,
        customer_name=customer_name,
    )
    
    if not appointment:
        return f"Sorry, the slot at {time} on {date} is not available at {dealer.name}."

    return (
        f"✓ Appointment confirmed!\n"
        f"  Confirmation ID: {appointment.id}\n"
        f"  Dealership: **{dealer.name}**\n"
        f"  Address: {dealer.address}\n"
        f"  Phone: {dealer.phone}\n"
        f"  Service: {appointment.service}\n"
        f"  Date: {appointment.date}\n"
        f"  Time: {appointment.time}\n"
        + (f"  Customer: {appointment.customer_name}\n" if appointment.customer_name else "")
    )


@tool
def get_my_bookings() -> str:
    """
    Get all current bookings/appointments.
    Use this when user asks about their bookings, reservations, or appointments.

    Returns:
        List of all current bookings with details.
    """
    bookings = _get_bookings()

    if not bookings:
        return "You have no bookings at this time."

    output_lines = [f"You have {len(bookings)} booking(s):\n"]
    for apt in bookings:
        dealer = get_dealership_by_id(apt.dealership_id)
        dealer_name = dealer.name if dealer else apt.dealership_id
        dealer_address = dealer.address if dealer else "N/A"
        output_lines.append(f"- Booking {apt.id}")
        output_lines.append(f"  Dealership: **{dealer_name}**")
        output_lines.append(f"  Address: {dealer_address}")
        output_lines.append(f"  Service: {apt.service}")
        output_lines.append(f"  Date: {apt.date}")
        output_lines.append(f"  Time: {apt.time}")
        if apt.customer_name:
            output_lines.append(f"  Customer: {apt.customer_name}")
        output_lines.append("")

    return "\n".join(output_lines)


@tool
def cancel_my_booking(booking_id: str) -> str:
    """
    Cancel an existing booking.
    Use this when user wants to cancel a reservation.

    Args:
        booking_id: The booking ID to cancel (e.g., "apt_0001")

    Returns:
        Confirmation of cancellation or error message.
    """
    apt = _get_booking_by_id(booking_id)
    if not apt:
        return f"Booking '{booking_id}' not found."

    dealer = get_dealership_by_id(apt.dealership_id)
    dealer_name = dealer.name if dealer else apt.dealership_id

    if _cancel_booking(booking_id):
        return (
            f"Booking cancelled successfully!\n"
            f"  Cancelled: {booking_id}\n"
            f"  Dealership: {dealer_name}\n"
            f"  Date: {apt.date}\n"
            f"  Time: {apt.time}\n"
        )
    return f"Failed to cancel booking '{booking_id}'."


@tool
def modify_my_booking(
    booking_id: str,
    new_date: Optional[str] = None,
    new_time: Optional[str] = None,
) -> str:
    """
    Modify an existing booking's date and/or time.
    Use this when user wants to change/modify/reschedule a reservation.

    Args:
        booking_id: The booking ID to modify (e.g., "apt_0001")
        new_date: New date for the appointment (format: YYYY-MM-DD)
        new_time: New time for the appointment (format: HH:MM)

    Returns:
        Confirmation of modification or error message.
    """
    apt = _get_booking_by_id(booking_id)
    if not apt:
        return f"Booking '{booking_id}' not found."

    if not new_date and not new_time:
        return "Please specify a new date and/or time for the booking."

    dealer = get_dealership_by_id(apt.dealership_id)
    dealer_name = dealer.name if dealer else apt.dealership_id

    modified = _modify_booking(booking_id, new_date, new_time)
    if modified:
        return (
            f"Booking modified successfully!\n"
            f"  Booking ID: {modified.id}\n"
            f"  Dealership: {dealer_name}\n"
            f"  Service: {modified.service}\n"
            f"  New Date: {modified.date}\n"
            f"  New Time: {modified.time}\n"
        )

    target_date = new_date or apt.date
    target_time = new_time or apt.time
    return f"Sorry, the slot at {target_time} on {target_date} is not available at {dealer_name}."


# List of all available tools for the agent
TOOLS = [
    get_dealership_info,
    search_dealerships,
    check_availability,
    compare_availability,
    book_next_available,
    book_appointment,
    get_my_bookings,
    cancel_my_booking,
    modify_my_booking,
]
