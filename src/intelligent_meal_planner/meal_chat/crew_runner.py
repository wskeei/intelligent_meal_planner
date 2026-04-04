from __future__ import annotations

import json

from .crew_factory import build_meal_planning_crew
from .crew_models import CrewBundle, CrewEvent, CrewPlanningResult
from .target_ranges import build_target_ranges


class CrewMealPlannerRunner:
    def __init__(self, crew_factory=build_meal_planning_crew, planning_tool=None):
        self.crew_factory = crew_factory
        self.planning_tool = planning_tool

    def run(self, memory, user) -> dict:
        bundle_or_crew = self.crew_factory(self.planning_tool)
        crew = bundle_or_crew.crew if isinstance(bundle_or_crew, CrewBundle) else bundle_or_crew
        kickoff_result = crew.kickoff(inputs=self._build_inputs(memory, user))
        parsed = self._parse_result(kickoff_result, bundle_or_crew, memory)
        return {
            "phase": "finalized",
            "assistant_message": parsed.final_message,
            "meal_plan": parsed.meal_plan,
            "events": [event.model_dump(mode="json") for event in parsed.events],
        }

    def _build_inputs(self, memory, user) -> dict:
        profile = dict(memory.profile)
        preferences = dict(memory.preferences)
        hidden_targets = self._build_hidden_targets(memory)
        return {
            "user_id": getattr(user, "id", None),
            "profile": profile,
            "preferences": preferences,
            "health_goal": preferences.get("health_goal", "healthy"),
            "budget": float(preferences.get("budget", 0) or 0),
            "disliked_foods": preferences.get("disliked_foods", []),
            "preferred_tags": preferences.get("preferred_tags", []),
            "hidden_targets": hidden_targets,
        }

    def _build_hidden_targets(self, memory) -> dict:
        ranges = memory.target_ranges
        if ranges is None and memory.profile and memory.preferences.get("health_goal"):
            ranges = build_target_ranges(
                profile=memory.profile,
                goal=memory.preferences.get("health_goal", "healthy"),
            )

        if ranges is None:
            return {
                "target_calories": 1800,
                "target_protein": 100,
                "target_carbs": 180,
                "target_fat": 55,
            }

        return {
            "target_calories": int((ranges.calories_min + ranges.calories_max) / 2),
            "target_protein": int((ranges.protein_min + ranges.protein_max) / 2),
            "target_carbs": int((ranges.carbs_min + ranges.carbs_max) / 2),
            "target_fat": int((ranges.fat_min + ranges.fat_max) / 2),
        }

    def _parse_result(self, kickoff_result, bundle_or_crew, memory) -> CrewPlanningResult:
        if isinstance(kickoff_result, CrewPlanningResult):
            return kickoff_result

        if isinstance(kickoff_result, dict):
            return CrewPlanningResult.model_validate(
                {
                    "final_message": kickoff_result.get("final_message", "方案完成"),
                    "meal_plan": kickoff_result.get("meal_plan") or {},
                    "events": kickoff_result.get("events") or self._fallback_events(bundle_or_crew),
                    "negotiation_summary": kickoff_result.get("negotiation_summary"),
                }
            )

        parsed = self._parse_crewai_output(kickoff_result)
        if parsed is not None:
            return parsed

        meal_plan = self._fallback_meal_plan(memory)
        return CrewPlanningResult(
            final_message="多智能体协作已完成，我给你整理好了方案。",
            meal_plan=meal_plan,
            events=self._fallback_events(bundle_or_crew),
        )

    def _parse_crewai_output(self, kickoff_result) -> CrewPlanningResult | None:
        for attr in ("pydantic", "json_dict"):
            value = getattr(kickoff_result, attr, None)
            if value:
                return CrewPlanningResult.model_validate(value)

        raw = getattr(kickoff_result, "raw", None)
        if isinstance(raw, str):
            try:
                return CrewPlanningResult.model_validate(json.loads(raw))
            except (json.JSONDecodeError, ValueError, TypeError):
                return None
        return None

    def _fallback_meal_plan(self, memory) -> dict:
        if self.planning_tool is None:
            return {}

        inputs = self._build_inputs(memory, user=None)
        return self.planning_tool.generate(
            goal=inputs["health_goal"],
            budget=inputs["budget"],
            disliked_foods=inputs["disliked_foods"],
            preferred_tags=inputs["preferred_tags"],
            hidden_targets=inputs["hidden_targets"],
        )

    def _fallback_events(self, bundle_or_crew) -> list[CrewEvent]:
        if isinstance(bundle_or_crew, CrewBundle):
            return [
                CrewEvent(
                    agent=agent.role,
                    status="completed",
                    message=bundle_or_crew.event_messages.get(agent.role, f"{agent.role} 已完成"),
                )
                for agent in bundle_or_crew.agents
            ]

        agents = getattr(bundle_or_crew, "agents", []) or []
        return [
            CrewEvent(
                agent=getattr(agent, "role", "Agent"),
                status="completed",
                message=f"{getattr(agent, 'role', 'Agent')} 已完成",
            )
            for agent in agents
        ]
