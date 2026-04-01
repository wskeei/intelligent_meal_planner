"""
Deprecated runtime entry. Final meal generation is now handled by the
strict-budget planner in `api.services.StrictBudgetPlanner`.
"""


class RLChefAgent:
    """Deprecated compatibility stub for the removed single-turn planner flow."""

    @staticmethod
    def create(*_args, **_kwargs):
        raise RuntimeError(
            "RLChefAgent is deprecated. Final plan generation now happens via "
            "the strict-budget conversational planner."
        )
