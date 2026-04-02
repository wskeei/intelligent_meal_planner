from intelligent_meal_planner.meal_chat.target_ranges import build_target_ranges


def test_build_target_ranges_for_weight_loss_returns_ranges_not_point_values():
    ranges = build_target_ranges(
        profile={
            "gender": "male",
            "age": 30,
            "height": 175,
            "weight": 82,
            "activity_level": "moderate",
        },
        goal="lose_weight",
    )

    assert ranges.calories_min < ranges.calories_max
    assert ranges.protein_min < ranges.protein_max
    assert ranges.strategy == "fat_loss"
    assert 1600 <= ranges.calories_min <= 2400


def test_build_target_ranges_uses_safe_defaults_when_profile_missing():
    ranges = build_target_ranges(
        profile={
            "gender": None,
            "age": None,
            "height": None,
            "weight": None,
            "activity_level": None,
        },
        goal="healthy",
    )

    assert ranges.calories_min >= 1200
    assert ranges.calories_max <= 2600
    assert ranges.protein_min >= 60
