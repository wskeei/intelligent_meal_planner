from __future__ import annotations

from pydantic import BaseModel, Field

from .session_schema import NegotiationOption, TargetRanges


class NegotiationResult(BaseModel):
    phase: str
    explanation: str
    recommended_budget_min: float
    recommended_budget_comfort: float
    options: list[NegotiationOption] = Field(default_factory=list)


def _estimate_budget_band(budget: float, protein_min: int) -> tuple[float, float]:
    protein_pressure = max(0, protein_min - 70)
    recommended_budget_min = max(float(budget), 80.0 + protein_pressure * 1.2)
    recommended_budget_comfort = recommended_budget_min + 30.0
    return recommended_budget_min, recommended_budget_comfort


def build_negotiation_result(
    budget: float, target_ranges: TargetRanges, locale: str = "zh"
) -> NegotiationResult:
    recommended_budget_min, recommended_budget_comfort = _estimate_budget_band(
        budget=budget,
        protein_min=target_ranges.protein_min,
    )

    if budget >= recommended_budget_min:
        explanation = (
            "The current budget is enough to move into final planning."
            if locale == "en"
            else "当前预算可以进入正式配餐。"
        )
        return NegotiationResult(
            phase="planning",
            explanation=explanation,
            recommended_budget_min=recommended_budget_min,
            recommended_budget_comfort=recommended_budget_comfort,
            options=[],
        )

    if locale == "en":
        explanation = (
            f"For your current goal, a budget of {budget:.0f} works better as a compromise plan. "
            f"The minimum recommended budget is about {recommended_budget_min:.0f}, "
            f"and a more comfortable budget is about {recommended_budget_comfort:.0f}."
        )
        budget_cut_title = "Budget-first option"
        budget_cut_rationale = "Prioritize staying within budget and calories, while keeping protein as high as possible."
        protein_priority_title = "Protein-first option"
        protein_priority_rationale = "Prioritize protein intake even if the cost moves closer to the upper budget limit."
    else:
        explanation = (
            f"按你当前目标，{budget:.0f} 元更适合做折中方案。"
            f" 最低建议预算约 {recommended_budget_min:.0f} 元，"
            f" 更从容的预算约 {recommended_budget_comfort:.0f} 元。"
        )
        budget_cut_title = "保守减脂"
        budget_cut_rationale = "优先控热量和预算，蛋白尽量高但允许略低。"
        protein_priority_title = "高蛋白优先"
        protein_priority_rationale = "优先保蛋白，价格更贴近预算上限。"

    return NegotiationResult(
        phase="negotiating",
        explanation=explanation,
        recommended_budget_min=recommended_budget_min,
        recommended_budget_comfort=recommended_budget_comfort,
        options=[
            NegotiationOption(
                key="budget_cut",
                title=budget_cut_title,
                rationale=budget_cut_rationale,
                budget=budget,
                preferred_tags=["light"],
            ),
            NegotiationOption(
                key="protein_priority",
                title=protein_priority_title,
                rationale=protein_priority_rationale,
                budget=max(
                    budget, min(recommended_budget_min, recommended_budget_comfort)
                ),
                preferred_tags=["high_protein"],
            ),
        ],
    )
