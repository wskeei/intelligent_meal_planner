from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass
class CrewBundle:
    crew: Crew
    agents: list[Agent]
    tasks: list[Task]
    event_messages: dict[str, str] = field(default_factory=dict)
