from unittest.mock import AsyncMock

import pytest

from app.sdk.client import MiraClient
from app.sdk.decorators import instrument_prediction


@pytest.mark.asyncio
async def test_instrument_prediction_decorator() -> None:
    client = MiraClient("http://localhost:8000", "token")
    client.send_event = AsyncMock(return_value={"ok": True})  # type: ignore[method-assign]

    @instrument_prediction(client)
    async def predict(**kwargs):
        return {"recommended_products": [{"product_id": "sku-1", "stock": 1}]}

    result = await predict(prompt="hello", agent_version="v1")

    assert "recommended_products" in result
    client.send_event.assert_awaited_once()
