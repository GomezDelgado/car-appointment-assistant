"""GraphQL schema using Strawberry."""

import strawberry
from typing import Optional

from src.agent.graph import chat
from src.data.mock_data import (
    DEALERSHIPS,
    search_dealerships as _search_dealerships,
    get_availability as _get_availability,
    Dealership as DealershipData,
    TimeSlot as TimeSlotData,
)


@strawberry.type
class Dealership:
    """A car dealership."""
    id: str
    name: str
    location: str
    services: list[str]
    phone: str


@strawberry.type
class TimeSlot:
    """An available appointment time slot."""
    dealership_id: str
    date: str
    time: str
    available: bool


@strawberry.type
class ChatResponse:
    """Response from the chat assistant."""
    message: str
    success: bool


@strawberry.type
class Query:
    """GraphQL queries."""
    
    @strawberry.field
    def dealerships(
        self,
        location: Optional[str] = None,
        service: Optional[str] = None,
    ) -> list[Dealership]:
        """Get list of dealerships, optionally filtered by location or service."""
        results = _search_dealerships(location=location, service=service)
        return [
            Dealership(
                id=d.id,
                name=d.name,
                location=d.location,
                services=d.services,
                phone=d.phone,
            )
            for d in results
        ]
    
    @strawberry.field
    def availability(
        self,
        dealership_id: str,
        date: Optional[str] = None,
    ) -> list[TimeSlot]:
        """Get available time slots for a dealership."""
        results = _get_availability(dealership_id=dealership_id, date=date)
        return [
            TimeSlot(
                dealership_id=s.dealership_id,
                date=s.date,
                time=s.time,
                available=s.available,
            )
            for s in results
        ]


@strawberry.type
class Mutation:
    """GraphQL mutations."""
    
    @strawberry.mutation
    async def chat(self, message: str) -> ChatResponse:
        """Send a message to the appointment assistant and get a response."""
        try:
            response = await chat(message)
            return ChatResponse(message=response, success=True)
        except Exception as e:
            return ChatResponse(message=f"Error: {str(e)}", success=False)


# Create the schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
