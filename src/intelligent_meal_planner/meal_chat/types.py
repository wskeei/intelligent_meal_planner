from typing import Optional

from pydantic import BaseModel, Field

from .session_schema import ConversationMemory, NegotiationOption


class ExtractionDebug(BaseModel):
    expected_slot: Optional[str] = None
    raw_response: str = ""
    payload: dict = Field(default_factory=dict)
    fallback_applied: bool = False


class ParsedTurn(BaseModel):
    profile_updates: dict = Field(default_factory=dict)
    preference_updates: dict = Field(default_factory=dict)
    acknowledged_restrictions: bool = False
    confidence: float | None = None
    missing_fields: list[str] = Field(default_factory=list)
    contradiction_fields: list[str] = Field(default_factory=list)
    debug: ExtractionDebug = Field(default_factory=ExtractionDebug)


class IntakeTurnResult(BaseModel):
    phase: str
    assistant_message: str
    memory: ConversationMemory
    ready_for_crew: bool = False
    crew_payload: dict | None = None


class CrewTurnResult(BaseModel):
    phase: str
    assistant_message: str
    memory: ConversationMemory
    negotiation_options: list[NegotiationOption] = Field(default_factory=list)
    meal_plan: dict | None = None
