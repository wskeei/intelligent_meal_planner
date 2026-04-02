from __future__ import annotations

from pydantic import BaseModel, Field


class CanonicalPreferences(BaseModel):
    health_goal: str | None = None
    budget: float | None = None
    disliked_foods: list[str] = Field(default_factory=list)
    preferred_tags: list[str] = Field(default_factory=list)


class UnderstandingAnalysis(BaseModel):
    confidence: float
    missing_fields: list[str] = Field(default_factory=list)
    contradiction_fields: list[str] = Field(default_factory=list)
    clarification_reason: str | None = None
    ready_for_negotiation: bool = False


class FollowUpPlan(BaseModel):
    questions: list[str] = Field(default_factory=list)
    assistant_message: str
