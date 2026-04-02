"""Client SDK for Claire observability."""

from app.sdk.client import ClaireClient
from app.sdk.decorators import instrument_prediction

__all__ = ["ClaireClient", "instrument_prediction"]
