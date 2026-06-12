"""SSE event models and formatting."""
import json
from pydantic import BaseModel


class SSEEvent(BaseModel):
    """A single SSE event with type and data payload."""
    type: str
    data: dict


def format_sse(event_type: str, data: dict) -> str:
    """Format a dict as a standard SSE event string.

    Returns: 'event: <type>\\ndata: <json>\\n\\n'
    """
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"
