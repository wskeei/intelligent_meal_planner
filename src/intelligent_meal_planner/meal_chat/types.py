from typing import Optional

from pydantic import BaseModel, Field


class ExtractionDebug(BaseModel):
    expected_slot: Optional[str] = None
    raw_response: str = ""
    payload: dict = Field(default_factory=dict)
    fallback_applied: bool = False


class ParsedTurn(BaseModel):
    profile_updates: dict = Field(default_factory=dict)
    preference_updates: dict = Field(default_factory=dict)
    acknowledged_restrictions: bool = False
    debug: ExtractionDebug = Field(default_factory=ExtractionDebug)
