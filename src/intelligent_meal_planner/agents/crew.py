"""
This module is retained only for backward reference.
Runtime meal planning has moved to the conversational orchestrator in
`intelligent_meal_planner.meal_chat.orchestrator`.
"""


class MealPlanningCrew:
    """Deprecated compatibility stub for the removed single-turn crew flow."""

    def __init__(self, *_args, **_kwargs):
        raise RuntimeError(
            "MealPlanningCrew is deprecated. Use the conversational meal-chat "
            "session flow instead."
        )
