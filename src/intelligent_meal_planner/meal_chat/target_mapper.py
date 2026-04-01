ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_MACROS = {
    "lose_weight": (0.35, 0.30, 0.35),
    "gain_muscle": (0.30, 0.45, 0.25),
    "maintain": (0.30, 0.40, 0.30),
    "healthy": (0.25, 0.45, 0.30),
}


def _clamp(value, low, high):
    return max(low, min(high, int(round(value))))


def build_hidden_targets(profile: dict, goal: str) -> dict:
    weight = profile["weight"]
    height = profile["height"]
    age = profile["age"]
    gender = profile["gender"]

    base = (10 * weight) + (6.25 * height) - (5 * age)
    bmr = base + 5 if gender == "male" else base - 161
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(profile["activity_level"], 1.2)

    if goal == "lose_weight":
        calories = tdee - 500
    elif goal == "gain_muscle":
        calories = tdee + 300
    else:
        calories = tdee

    calories = _clamp(calories, 1200, 3000)
    protein_ratio, carb_ratio, fat_ratio = GOAL_MACROS.get(goal, GOAL_MACROS["healthy"])

    return {
        "target_calories": calories,
        "target_protein": _clamp((calories * protein_ratio) / 4, 60, 220),
        "target_carbs": _clamp((calories * carb_ratio) / 4, 50, 400),
        "target_fat": _clamp((calories * fat_ratio) / 9, 30, 120),
    }
