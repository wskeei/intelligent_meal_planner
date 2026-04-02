from __future__ import annotations

from .session_schema import ConversationMemory
from .understanding_schema import FollowUpPlan, UnderstandingAnalysis

QUESTION_PROMPTS = {
    "gender": "先确认一下你的性别，这样我好把基础代谢估得更准。",
    "age": "你今年大概多少岁？我会据此调整热量范围。",
    "height": "你的身高大概多少厘米？",
    "weight": "你现在体重大概多少公斤？",
    "activity_level": "你平时活动量怎么样，久坐还是会训练？",
    "health_goal": "这次你更想减脂、增肌，还是先维持住？",
    "budget": "你一天的预算大概想控制在多少？这样我才能判断食材密度和蛋白空间。",
}


def build_follow_up_plan(
    memory: ConversationMemory,
    analysis: UnderstandingAnalysis,
) -> FollowUpPlan:
    if analysis.missing_fields:
        questions = analysis.missing_fields[:2]
        prompt = (
            "我先补齐两个关键点，这样后面的分析、配餐和方案判断会更准。 "
            + " ".join(QUESTION_PROMPTS[field] for field in questions)
        )
        return FollowUpPlan(questions=questions, assistant_message=prompt)

    if analysis.clarification_reason == "low_confidence":
        return FollowUpPlan(
            questions=["health_goal", "budget"],
            assistant_message=(
                f"我先确认一下，我现在是按“{memory.preferences.get('health_goal')}”和 "
                f"{memory.preferences.get('budget')} 元预算理解的，对吗？"
            ),
        )

    if analysis.clarification_reason == "contradiction_detected":
        goal = memory.preferences.get("health_goal")
        goal_text = {
            "lose_weight": "减脂",
            "gain_muscle": "增肌",
            "maintain": "维持",
            "healthy": "健康饮食",
        }.get(goal, goal or "当前目标")
        return FollowUpPlan(
            questions=["health_goal"],
            assistant_message=(
                f"我听起来有一点矛盾：你像是在追求{goal_text}，但同时又提到想把进食压低。"
                " 你这次更优先的是体脂下降，还是肌肉增长？"
            ),
        )

    return FollowUpPlan(questions=[], assistant_message="我们可以继续往下分析。")
