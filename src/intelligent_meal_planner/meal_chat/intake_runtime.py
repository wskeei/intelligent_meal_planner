from __future__ import annotations

from .crew_runtime import CrewMealChatRuntime
from .question_strategy import build_follow_up_plan
from .target_ranges import build_target_ranges
from .types import IntakeTurnResult
from .understanding_analyzer import analyze_understanding


class IntakeRuntime(CrewMealChatRuntime):
    def __init__(self, extractor=None):
        super().__init__(planning_tool=None, extractor=extractor)

    def run_turn(self, user_message: str, memory):
        intent = self.intent_agent(user_message=user_message, memory=memory)
        profile_delta = self.profile_agent(
            user_message=user_message,
            memory=memory,
            intent=intent,
        )
        updated = self._merge_memory(memory, profile_delta)
        analysis = analyze_understanding(
            memory=updated,
            confidence=self._resolve_analysis_confidence(memory, profile_delta),
            extracted_missing_fields=profile_delta.get("missing_fields", []),
            contradiction_fields=profile_delta.get("contradiction_fields", []),
        )
        updated.analysis = analysis
        updated.known_facts["preference_confidence"] = analysis.confidence
        updated.known_facts["missing_fields"] = analysis.missing_fields
        updated.known_facts["contradiction_fields"] = analysis.contradiction_fields
        updated.known_facts["clarification_reason"] = analysis.clarification_reason

        if not analysis.ready_for_negotiation:
            self._prioritize_intake_questions(updated)
            follow_up = build_follow_up_plan(memory=updated, analysis=analysis)
            updated.follow_up_plan = follow_up
            updated.open_questions = follow_up.questions
            if follow_up.questions or follow_up.assistant_message:
                updated.clarification_history.append(follow_up)
            updated.phase = "discovering"
            return IntakeTurnResult(
                phase="discovering",
                assistant_message=follow_up.assistant_message,
                memory=updated,
                ready_for_crew=False,
            )

        updated.follow_up_plan = None
        updated.open_questions = []
        updated.phase = "planning_ready"
        if updated.profile and updated.preferences.get("health_goal"):
            updated.target_ranges = build_target_ranges(
                profile=updated.profile,
                goal=updated.preferences.get("health_goal", "healthy"),
            )
        return IntakeTurnResult(
            phase="planning_ready",
            assistant_message="信息已经齐了，我现在组织多智能体为你生成方案。",
            memory=updated,
            ready_for_crew=True,
            crew_payload=updated.model_dump(mode="json"),
        )

    def _prioritize_intake_questions(self, memory) -> None:
        analysis = memory.analysis
        if analysis is None or not analysis.missing_fields:
            return

        priority_fields = ("budget", "health_goal", "disliked_foods", "preferred_tags")
        prioritized = [
            field for field in priority_fields if field in analysis.missing_fields
        ]
        prioritized.extend(
            field for field in analysis.missing_fields if field not in prioritized
        )
        analysis.missing_fields = prioritized
