from __future__ import annotations

from .session_schema import TargetRanges


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def _clamp(value: float, low: int, high: int) -> int:
    return max(low, min(high, int(round(value))))


def build_target_ranges(profile: dict, goal: str) -> TargetRanges:
    weight = float(profile.get("weight") or 70)
    height = float(profile.get("height") or 170)
    age = int(profile.get("age") or 30)
    gender = profile.get("gender") or "female"
    activity_level = profile.get("activity_level") or "light"

    base = (10 * weight) + (6.25 * height) - (5 * age)
    bmr = base + 5 if gender == "male" else base - 161
    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity_level, ACTIVITY_MULTIPLIERS["light"])

    if goal == "lose_weight":
        center = tdee - 450
        strategy = "fat_loss"
        protein_per_kg = (1.6, 2.0)
        fat_ratio = (0.20, 0.30)
    elif goal == "gain_muscle":
        center = tdee + 250
        strategy = "muscle_gain"
        protein_per_kg = (1.8, 2.2)
        fat_ratio = (0.20, 0.30)
    else:
        center = tdee
        strategy = "balanced"
        protein_per_kg = (1.2, 1.8)
        fat_ratio = (0.25, 0.35)

    calories_min = _clamp(center - 150, 1200, 3000)
    calories_max = max(calories_min, _clamp(center + 150, 1200, 3000))
    protein_min = _clamp(weight * protein_per_kg[0], 60, 220)
    protein_max = max(protein_min, _clamp(weight * protein_per_kg[1], 60, 220))
    fat_min = _clamp(calories_min * fat_ratio[0] / 9, 30, 120)
    fat_max = max(fat_min, _clamp(calories_max * fat_ratio[1] / 9, 30, 120))
    carbs_min = _clamp((calories_min - protein_max * 4 - fat_max * 9) / 4, 50, 400)
    carbs_max = max(
        carbs_min, _clamp((calories_max - protein_min * 4 - fat_min * 9) / 4, 50, 400)
    )

    return TargetRanges(
        calories_min=calories_min,
        calories_max=calories_max,
        protein_min=protein_min,
        protein_max=protein_max,
        carbs_min=carbs_min,
        carbs_max=carbs_max,
        fat_min=fat_min,
        fat_max=fat_max,
        strategy=strategy,
    )
