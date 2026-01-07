"""Mock data for car dealerships and appointments."""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional


@dataclass
class Dealership:
    id: str
    name: str
    location: str
    services: list[str]
    phone: str


@dataclass
class TimeSlot:
    dealership_id: str
    date: str
    time: str
    available: bool


@dataclass
class Appointment:
    id: str
    dealership_id: str
    service: str
    date: str
    time: str
    customer_name: Optional[str] = None


# Mock dealerships (New York City area)
DEALERSHIPS: list[Dealership] = [
    Dealership(
        id="dealer_001",
        name="Downtown Auto Service",
        location="Manhattan",
        services=["oil_change", "tire_rotation", "brake_inspection", "general_review"],
        phone="+1 212 555 0101",
    ),
    Dealership(
        id="dealer_002",
        name="Brooklyn CarCare",
        location="Brooklyn",
        services=["oil_change", "tire_rotation", "state_inspection", "air_conditioning"],
        phone="+1 718 555 0102",
    ),
    Dealership(
        id="dealer_003",
        name="Queens Auto Pro",
        location="Queens",
        services=["oil_change", "general_review", "brake_inspection", "battery_check"],
        phone="+1 718 555 0103",
    ),
    Dealership(
        id="dealer_004",
        name="Bronx Mechanics Plus",
        location="Bronx",
        services=["oil_change", "tire_rotation", "state_inspection", "general_review"],
        phone="+1 718 555 0104",
    ),
    Dealership(
        id="dealer_005",
        name="Midtown Motors",
        location="Manhattan",
        services=["oil_change", "air_conditioning", "battery_check", "state_inspection"],
        phone="+1 212 555 0105",
    ),
    Dealership(
        id="dealer_006",
        name="Bay Ridge Auto Center",
        location="Brooklyn",
        services=["oil_change", "brake_inspection", "general_review", "battery_check"],
        phone="+1 718 555 0106",
    ),
    Dealership(
        id="dealer_007",
        name="Astoria Car Service",
        location="Queens",
        services=["oil_change", "tire_rotation", "air_conditioning", "state_inspection"],
        phone="+1 718 555 0107",
    ),
    Dealership(
        id="dealer_008",
        name="Harlem Auto Works",
        location="Manhattan",
        services=["oil_change", "tire_rotation", "brake_inspection", "battery_check"],
        phone="+1 212 555 0108",
    ),
]

# Service name mappings (for natural language understanding)
SERVICE_MAPPINGS: dict[str, list[str]] = {
    "oil_change": ["oil change", "oil", "change oil", "oil service"],
    "tire_rotation": ["tire", "tires", "rotation", "wheel", "wheels"],
    "brake_inspection": ["brake", "brakes", "brake check", "brake inspection"],
    "general_review": ["review", "checkup", "maintenance", "general inspection"],
    "state_inspection": ["state inspection", "inspection", "vehicle inspection", "safety inspection"],
    "air_conditioning": ["ac", "air conditioning", "a/c", "cooling"],
    "battery_check": ["battery", "battery check", "battery test"],
}


def _generate_availability() -> list[TimeSlot]:
    """Generate mock availability for the next 14 days."""
    slots = []
    base_date = datetime.now()

    time_options = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]

    for dealer in DEALERSHIPS:
        for day_offset in range(1, 15):  # Next 14 days
            date = (base_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            for time in time_options:
                # Simulate some slots being taken (roughly 30% unavailable)
                available = hash(f"{dealer.id}{date}{time}") % 10 > 2
                slots.append(TimeSlot(
                    dealership_id=dealer.id,
                    date=date,
                    time=time,
                    available=available,
                ))
    
    return slots


# Generate availability on module load
AVAILABILITY: list[TimeSlot] = _generate_availability()

# Store for booked appointments
APPOINTMENTS: list[Appointment] = []


def normalize_service(user_input: str) -> Optional[str]:
    """Convert natural language service description to service ID."""
    user_input_lower = user_input.lower()
    for service_id, keywords in SERVICE_MAPPINGS.items():
        for keyword in keywords:
            if keyword in user_input_lower:
                return service_id
    return None


def search_dealerships(
    location: Optional[str] = None,
    service: Optional[str] = None,
) -> list[Dealership]:
    """Find dealerships by location and/or service."""
    results = DEALERSHIPS.copy()
    
    if location:
        location_lower = location.lower()
        results = [d for d in results if location_lower in d.location.lower()]
    
    if service:
        # Try to normalize the service first
        normalized = normalize_service(service) or service
        results = [d for d in results if normalized in d.services]
    
    return results


def get_availability(
    dealership_id: str,
    date: Optional[str] = None,
) -> list[TimeSlot]:
    """Get available time slots for a dealership."""
    slots = [s for s in AVAILABILITY if s.dealership_id == dealership_id and s.available]
    
    if date:
        slots = [s for s in slots if s.date == date]
    
    return slots


def book_appointment(
    dealership_id: str,
    service: str,
    date: str,
    time: str,
    customer_name: Optional[str] = None,
) -> Optional[Appointment]:
    """Book an appointment at a dealership."""
    # Check if slot is available
    for slot in AVAILABILITY:
        if (slot.dealership_id == dealership_id and 
            slot.date == date and 
            slot.time == time and 
            slot.available):
            # Mark slot as taken
            slot.available = False
            
            # Create appointment
            appointment = Appointment(
                id=f"apt_{len(APPOINTMENTS) + 1:04d}",
                dealership_id=dealership_id,
                service=normalize_service(service) or service,
                date=date,
                time=time,
                customer_name=customer_name,
            )
            APPOINTMENTS.append(appointment)
            return appointment
    
    return None


def get_dealership_by_id(dealership_id: str) -> Optional[Dealership]:
    """Get a dealership by its ID."""
    for dealer in DEALERSHIPS:
        if dealer.id == dealership_id:
            return dealer
    return None


def get_dealership_by_name(name: str) -> Optional[Dealership]:
    """Get a dealership by its name (case-insensitive, partial match)."""
    name_lower = name.lower()
    for dealer in DEALERSHIPS:
        if name_lower in dealer.name.lower():
            return dealer
    return None


def resolve_dealership(identifier: str) -> Optional[Dealership]:
    """Resolve a dealership by ID or name."""
    # First try by ID
    dealer = get_dealership_by_id(identifier)
    if dealer:
        return dealer
    # Then try by name
    return get_dealership_by_name(identifier)


def get_bookings() -> list[Appointment]:
    """Get all booked appointments."""
    return APPOINTMENTS.copy()


def get_booking_by_id(booking_id: str) -> Optional[Appointment]:
    """Get a specific booking by ID."""
    for apt in APPOINTMENTS:
        if apt.id == booking_id:
            return apt
    return None


def cancel_booking(booking_id: str) -> bool:
    """Cancel a booking and free up the time slot."""
    for i, apt in enumerate(APPOINTMENTS):
        if apt.id == booking_id:
            # Free up the time slot
            for slot in AVAILABILITY:
                if (slot.dealership_id == apt.dealership_id and
                    slot.date == apt.date and
                    slot.time == apt.time):
                    slot.available = True
                    break
            # Remove the appointment
            APPOINTMENTS.pop(i)
            return True
    return False


def modify_booking(
    booking_id: str,
    new_date: Optional[str] = None,
    new_time: Optional[str] = None,
) -> Optional[Appointment]:
    """Modify a booking's date and/or time."""
    apt = get_booking_by_id(booking_id)
    if not apt:
        return None

    target_date = new_date or apt.date
    target_time = new_time or apt.time

    # Check if new slot is available
    new_slot = None
    for slot in AVAILABILITY:
        if (slot.dealership_id == apt.dealership_id and
            slot.date == target_date and
            slot.time == target_time and
            slot.available):
            new_slot = slot
            break

    if not new_slot:
        return None

    # Free the old slot
    for slot in AVAILABILITY:
        if (slot.dealership_id == apt.dealership_id and
            slot.date == apt.date and
            slot.time == apt.time):
            slot.available = True
            break

    # Book the new slot
    new_slot.available = False
    apt.date = target_date
    apt.time = target_time

    return apt
