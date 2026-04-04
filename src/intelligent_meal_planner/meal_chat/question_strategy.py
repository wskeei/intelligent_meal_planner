from __future__ import annotations

from .copy import (
    continue_analysis,
    contradiction_prompt,
    follow_up_prompt_intro,
    low_confidence_prompt,
    prompt_for_field,
    resolve_locale,
)
from .session_schema import ConversationMemory
from .understanding_schema import FollowUpPlan, UnderstandingAnalysis


def build_follow_up_plan(
    memory: ConversationMemory,
    analysis: UnderstandingAnalysis,
) -> FollowUpPlan:
    locale = resolve_locale(memory)

    if analysis.missing_fields:
        questions = analysis.missing_fields[:2]
        prompt = " ".join(
            [follow_up_prompt_intro(locale)]
            + [prompt_for_field(field, locale) for field in questions]
        )
        return FollowUpPlan(questions=questions, assistant_message=prompt)

    if analysis.clarification_reason == "low_confidence":
        return FollowUpPlan(
            questions=["health_goal", "budget"],
            assistant_message=low_confidence_prompt(
                goal=memory.preferences.get("health_goal"),
                budget=memory.preferences.get("budget"),
                locale=locale,
            ),
        )

    if analysis.clarification_reason == "contradiction_detected":
        return FollowUpPlan(
            questions=["health_goal"],
            assistant_message=contradiction_prompt(
                goal=memory.preferences.get("health_goal"),
                locale=locale,
            ),
        )

    return FollowUpPlan(questions=[], assistant_message=continue_analysis(locale))
