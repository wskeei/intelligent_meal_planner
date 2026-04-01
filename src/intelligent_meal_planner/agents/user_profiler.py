"""
Deprecated runtime entry. Profile collection is now handled by the
conversational session orchestrator and DeepSeek slot extractor.
"""


class UserProfilerAgent:
    """Deprecated compatibility stub for the removed single-turn agent flow."""

    @staticmethod
    def create(*_args, **_kwargs):
        raise RuntimeError(
            "UserProfilerAgent is deprecated. Profile collection now happens "
            "inside the conversational meal-chat flow."
        )
