"""Domain exceptions for the API service layer.

These exceptions carry business-logic meaning without HTTP semantics.
Routers catch them and map to appropriate HTTP status codes.
"""


class WeeklyPlanNotFoundError(Exception):
    pass


class WeeklyPlanDayNotFoundError(Exception):
    pass


class DayAlreadyConfirmedError(Exception):
    pass


class DayNotConfirmedError(Exception):
    pass


class EmptyMealPlanError(Exception):
    pass


class RecipeMissingError(Exception):
    def __init__(self, recipe_id: int | None = None):
        self.recipe_id = recipe_id
        super().__init__(f"Recipe data missing for planned meal (id={recipe_id})")
