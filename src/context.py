"""Context variables for the application."""

from contextvars import ContextVar

# Session ID for the current request
current_session_id: ContextVar[str] = ContextVar("current_session_id", default="default")


def get_session_id() -> str:
    """Get the current session ID."""
    return current_session_id.get()


def set_session_id(session_id: str) -> None:
    """Set the current session ID."""
    current_session_id.set(session_id)
