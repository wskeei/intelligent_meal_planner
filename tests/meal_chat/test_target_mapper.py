from intelligent_meal_planner.meal_chat.target_mapper import build_hidden_targets


def test_weight_loss_mapping_is_clamped_and_high_protein():
    profile = {
        "gender": "male",
        "age": 26,
        "height": 178,
        "weight": 80,
        "activity_level": "moderate",
    }

    targets = build_hidden_targets(profile, "lose_weight")

    assert 1200 <= targets["target_calories"] <= 3000
    assert 60 <= targets["target_protein"] <= 220
    assert 50 <= targets["target_carbs"] <= 400
    assert 30 <= targets["target_fat"] <= 120
    assert targets["target_protein"] > targets["target_fat"]


def test_gain_muscle_mapping_prefers_higher_carbs():
    profile = {
        "gender": "female",
        "age": 24,
        "height": 165,
        "weight": 58,
        "activity_level": "active",
    }

    targets = build_hidden_targets(profile, "gain_muscle")

    assert targets["target_carbs"] > targets["target_fat"]
