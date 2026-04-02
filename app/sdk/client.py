from typing import Any

import httpx


class ClaireClient:
    def __init__(self, base_url: str, api_token: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Token": api_token}
        self.timeout = timeout

    async def send_event(self, event: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/events",
                json=event,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_anomalies(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/v1/anomalies", headers=self.headers)
            response.raise_for_status()
            return response.json()
