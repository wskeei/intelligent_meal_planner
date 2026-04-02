from intelligent_meal_planner.meal_chat.semantic_normalizer import (
    normalize_budget,
    normalize_goal,
    normalize_preference_lists,
)


def test_normalize_budget_understands_freeform_chinese_budget_phrases():
    assert normalize_budget("控制在两百以内") == 200.0
    assert normalize_budget("预算别太贵，150左右") == 150.0
    assert normalize_budget("一百五上下都可以") == 150.0


def test_normalize_goal_understands_colloquial_goal_phrases():
    assert normalize_goal("最近想把体脂往下压一点") == "lose_weight"
    assert normalize_goal("练壮一点，蛋白得跟上") == "gain_muscle"
    assert normalize_goal("先稳住别掉秤") == "maintain"
    assert normalize_goal("吃少一点，把体脂压下去") == "lose_weight"


def test_normalize_preference_lists_deduplicates_and_canonicalizes():
    normalized = normalize_preference_lists(
        disliked_foods="香菜, 芹菜, 香菜",
        preferred_tags=["清爽", "清淡", "高蛋白"],
    )

    assert normalized["disliked_foods"] == ["香菜", "芹菜"]
    assert normalized["preferred_tags"] == ["清淡", "高蛋白"]
