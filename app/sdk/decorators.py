import functools
from datetime import datetime
from typing import Any, Awaitable, Callable

from app.sdk.client import ClaireClient


def instrument_prediction(client: ClaireClient, *, event_type: str = "prediction") -> Callable:
    def decorator(
        func: Callable[..., Awaitable[dict[str, Any]]],
    ) -> Callable[..., Awaitable[dict[str, Any]]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            result = await func(*args, **kwargs)
            event = {
                "event_id": kwargs.get("event_id", f"evt-{datetime.utcnow().timestamp()}"),
                "event_type": event_type,
                "prompt": kwargs.get("prompt", ""),
                "context": kwargs.get("context", {}),
                "prediction": result,
                "metadata": {
                    "user_id_hash": kwargs.get("user_id_hash"),
                    "session_id": kwargs.get("session_id"),
                    "agent_version": kwargs.get("agent_version", "unknown"),
                    "source": kwargs.get("source", "sdk"),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }
            await client.send_event(event)
            return result

        return wrapper

    return decorator
