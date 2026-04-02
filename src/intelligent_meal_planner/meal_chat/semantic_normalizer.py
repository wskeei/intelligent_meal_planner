from __future__ import annotations

import re

GOAL_ALIASES = {
    "lose_weight": ("减肥", "减脂", "瘦一点", "控脂", "把体脂压下去", "体脂往下压"),
    "gain_muscle": ("增肌", "练壮一点", "练厚一点", "长肌肉"),
    "maintain": ("维持", "保持", "先稳住", "不想明显增减", "别掉秤"),
    "healthy": ("健康饮食", "吃干净点", "均衡一点"),
}

TAG_ALIASES = {
    "清爽": "清淡",
    "清淡": "清淡",
    "高蛋白": "高蛋白",
    "蛋白高一点": "高蛋白",
    "家常": "家常",
}

_BUDGET_VALUE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")
_CHINESE_AMOUNT_PATTERN = re.compile(r"[零一二两三四五六七八九十百千万]+")


def normalize_goal(text: str | None) -> str | None:
    if not text:
        return None

    normalized_text = str(text).strip()
    for goal, aliases in GOAL_ALIASES.items():
        if any(alias in normalized_text for alias in aliases):
            return goal
    return None


def parse_chinese_amount(text: str) -> int | None:
    digits = {
        "零": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }
    units = {
        "十": 10,
        "百": 100,
        "千": 1000,
        "万": 10000,
    }
    if not text:
        return None

    normalized = text.strip()
    if "百" in normalized and "十" not in normalized and normalized[-1] in digits:
        normalized = f"{normalized}十"
    if normalized.startswith("十"):
        normalized = f"一{normalized}"

    total = 0
    section = 0
    number = 0

    for char in normalized:
        if char in digits:
            number = digits[char]
            continue

        unit = units.get(char)
        if unit is None:
            continue

        if unit == 10000:
            section = (section + number) * unit
            total += section
            section = 0
            number = 0
            continue

        if number == 0:
            number = 1
        section += number * unit
        number = 0

    return total + section + number


def normalize_budget(value) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        return None

    text = str(value).replace(",", "").replace("俩", "两").strip()
    digit_match = _BUDGET_VALUE_PATTERN.search(text)
    if digit_match:
        return float(digit_match.group(1))

    amount_match = _CHINESE_AMOUNT_PATTERN.search(text)
    if amount_match is None:
        return None

    amount = parse_chinese_amount(amount_match.group(0))
    return float(amount) if amount is not None else None


def normalize_preference_lists(disliked_foods, preferred_tags) -> dict:
    disliked = _dedupe(_split_values(disliked_foods))
    tags = _dedupe(
        canonical
        for item in _split_values(preferred_tags)
        if (canonical := TAG_ALIASES.get(item))
    )
    return {
        "disliked_foods": disliked,
        "preferred_tags": tags,
    }


def _split_values(value) -> list[str]:
    if isinstance(value, list):
        values = value
    elif isinstance(value, str):
        values = re.split(r"[，,、/；;\s]+", value)
    else:
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def _dedupe(values) -> list[str]:
    return list(dict.fromkeys(values))
