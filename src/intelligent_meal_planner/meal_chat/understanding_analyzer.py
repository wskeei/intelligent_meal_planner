from __future__ import annotations

from .session_schema import ConversationMemory
from .understanding_schema import UnderstandingAnalysis

REQUIRED_PROFILE_FIELDS = ("gender", "age", "height", "weight", "activity_level")
REQUIRED_PREFERENCE_FIELDS = ("health_goal", "budget")
LOW_CONFIDENCE_THRESHOLD = 0.55


def analyze_understanding(
    memory: ConversationMemory,
    confidence: float,
    extracted_missing_fields: list[str],
    contradiction_fields: list[str] | None = None,
) -> UnderstandingAnalysis:
    missing_fields = list(
        dict.fromkeys(extracted_missing_fields + _find_missing_fields(memory))
    )
    contradiction_fields = contradiction_fields or []
    ready = (
        not missing_fields
        and not contradiction_fields
        and confidence >= LOW_CONFIDENCE_THRESHOLD
    )

    if contradiction_fields:
        reason = "contradiction_detected"
    elif missing_fields:
        reason = "missing_required_fields"
    elif confidence < LOW_CONFIDENCE_THRESHOLD:
        reason = "low_confidence"
    else:
        reason = None

    return UnderstandingAnalysis(
        confidence=round(confidence, 2),
        missing_fields=missing_fields,
        contradiction_fields=contradiction_fields,
        clarification_reason=reason,
        ready_for_negotiation=ready,
    )


def _find_missing_fields(memory: ConversationMemory) -> list[str]:
    missing_fields = [
        field for field in REQUIRED_PROFILE_FIELDS if memory.profile.get(field) in (None, "")
    ]
    missing_fields.extend(
        field
        for field in REQUIRED_PREFERENCE_FIELDS
        if memory.preferences.get(field) in (None, "")
    )
    return missing_fields
