from __future__ import annotations

from pydantic import BaseModel, Field


class TargetRanges(BaseModel):
    calories_min: int
    calories_max: int
    protein_min: int
    protein_max: int
    carbs_min: int
    carbs_max: int
    fat_min: int
    fat_max: int
    strategy: str


class NegotiationOption(BaseModel):
    key: str
    title: str
    rationale: str
    budget: float
    preferred_tags: list[str] = Field(default_factory=list)


class ConversationMemory(BaseModel):
    phase: str = "discovering"
    profile: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    known_facts: dict = Field(default_factory=dict)
    open_questions: list[str] = Field(default_factory=list)
    target_ranges: TargetRanges | None = None
    negotiation_options: list[NegotiationOption] = Field(default_factory=list)
    clarification_history: list[dict] = Field(default_factory=list)
