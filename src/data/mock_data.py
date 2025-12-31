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
    """Generate mock availability for the next 7 days."""
    slots = []
    base_date = datetime.now()
    
    time_options = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]
    
    for dealer in DEALERSHIPS:
        for day_offset in range(1, 8):  # Next 7 days
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
