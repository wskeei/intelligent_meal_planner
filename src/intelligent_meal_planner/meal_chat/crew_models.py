from __future__ import annotations

from dataclasses import dataclass

from crewai import Agent, Crew, Task
from pydantic import BaseModel


class CrewEvent(BaseModel):
    agent: str
    status: str
    message: str
    payload: dict | None = None


class CrewPlanningResult(BaseModel):
    final_message: str
    meal_plan: dict
    events: list[CrewEvent]
    negotiation_summary: dict | None = None


class RequirementReview(BaseModel):
    summary: str
    constraints: dict


class NutritionStrategy(BaseModel):
    summary: str
    target_ranges: dict


class BudgetCoordination(BaseModel):
    summary: str
    budget: float
    assessment: str


class DQNMealPlanArtifact(BaseModel):
    summary: str
    meal_plan: dict
    tool_name: str


@dataclass
class CrewBundle:
    crew: Crew
    agents: list[Agent]
    tasks: list[Task]
    runtime_llm: object | None = None
