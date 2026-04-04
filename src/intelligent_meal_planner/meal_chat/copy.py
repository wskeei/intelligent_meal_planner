from __future__ import annotations

from .session_schema import ConversationMemory


SUPPORTED_LOCALES = {"en", "zh"}

QUESTION_PROMPTS = {
    "zh": {
        "gender": "先确认一下你的性别，这样我好把基础代谢估得更准。",
        "age": "你今年大概多少岁？我会据此调整热量范围。",
        "height": "你的身高大概多少厘米？",
        "weight": "你现在体重大概多少公斤？",
        "activity_level": "你平时活动量怎么样，久坐还是会训练？",
        "health_goal": "这次你更想减脂、增肌，还是先维持住？",
        "budget": "你一天的预算大概想控制在多少？这样我才能判断食材密度和蛋白空间。",
    },
    "en": {
        "gender": "First, what gender should I use for a more realistic baseline estimate?",
        "age": "About how old are you? I use that to adjust your calorie range.",
        "height": "About how tall are you in centimeters?",
        "weight": "About how much do you weigh in kilograms right now?",
        "activity_level": "What is your usual activity level, mostly sedentary or regular training?",
        "health_goal": "Is this request mainly for fat loss, muscle gain, or maintenance?",
        "budget": "What daily budget do you want to stay within? That changes how much protein and ingredient density is realistic.",
    },
}

GOAL_TEXT = {
    "zh": {
        "lose_weight": "减脂",
        "gain_muscle": "增肌",
        "maintain": "维持",
        "healthy": "健康饮食",
    },
    "en": {
        "lose_weight": "fat loss",
        "gain_muscle": "muscle gain",
        "maintain": "maintenance",
        "healthy": "healthy eating",
    },
}


def normalize_locale(value: str | None) -> str:
    if not value:
        return "zh"

    token = value.lower().replace("_", "-")
    if token.startswith("en"):
        return "en"
    if token.startswith("zh"):
        return "zh"
    return "zh"


def resolve_locale(memory: ConversationMemory) -> str:
    locale = memory.known_facts.get("locale")
    if isinstance(locale, str):
        return normalize_locale(locale)
    return "zh"


def session_intro(locale: str) -> str:
    if locale == "en":
        return (
            "I will first confirm your goal, budget, and food preferences, "
            "then organize a realistic daily meal plan within budget."
        )
    return "我会先了解你的目标、预算和口味偏好，再帮你整理一份预算内的一日三餐方案。"


def follow_up_prompt_intro(locale: str) -> str:
    if locale == "en":
        return "I need two key details first so the analysis, planning, and tradeoffs stay accurate."
    return "我先补齐两个关键点，这样后面的分析、配餐和方案判断会更准。"


def prompt_for_field(field: str, locale: str) -> str:
    prompts = QUESTION_PROMPTS.get(locale, QUESTION_PROMPTS["zh"])
    return prompts.get(field, field)


def low_confidence_prompt(goal: str | None, budget: object, locale: str) -> str:
    if locale == "en":
        return (
            f"I want to confirm one thing: should I keep planning around "
            f'"{goal or "your current goal"}" and a budget of {budget}?'
        )
    return (
        f"我先确认一下，我现在是按“{goal}”和 {budget} 元预算理解的，对吗？"
    )


def contradiction_prompt(goal: str | None, locale: str) -> str:
    goal_text = GOAL_TEXT[locale].get(goal, goal or ("current goal" if locale == "en" else "当前目标"))
    if locale == "en":
        return (
            f"I hear a possible conflict: you sound like you want {goal_text}, "
            "but you also mentioned eating much less. Which matters more for this request?"
        )
    return (
        f"我听起来有一点矛盾：你像是在追求{goal_text}，但同时又提到想把进食压低。"
        " 你这次更优先的是体脂下降，还是肌肉增长？"
    )


def continue_analysis(locale: str) -> str:
    if locale == "en":
        return "We can keep moving forward from here."
    return "我们可以继续往下分析。"


def planning_ready(locale: str) -> str:
    if locale == "en":
        return "The key information is complete. I am now organizing the multi-agent planning step for you."
    return "信息已经齐了，我现在组织多智能体为你生成方案。"


def negotiation_missing_inputs(locale: str) -> str:
    if locale == "en":
        return "I still need your budget and goal before I can judge what is feasible."
    return "我还需要你的预算和目标信息，才能继续判断。"


def planning_tool_ready(locale: str) -> str:
    if locale == "en":
        return "I am ready to start building the meal plan."
    return "我已经准备好开始配餐。"


def dual_plan_ready(locale: str) -> str:
    if locale == "en":
        return "I prepared two plan directions for you."
    return "我给你整理了两套方案。"


def single_plan_ready(locale: str) -> str:
    if locale == "en":
        return "I prepared one complete plan for you."
    return "我给你整理好了一份方案。"
