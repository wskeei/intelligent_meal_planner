from __future__ import annotations

from pydantic import BaseModel, Field

from ..api.feasibility import estimate_budget_band
from .session_schema import NegotiationOption, TargetRanges


class NegotiationResult(BaseModel):
    phase: str
    explanation: str
    recommended_budget_min: float
    recommended_budget_comfort: float
    options: list[NegotiationOption] = Field(default_factory=list)


def build_negotiation_result(
    budget: float, target_ranges: TargetRanges
) -> NegotiationResult:
    recommended_budget_min, recommended_budget_comfort = estimate_budget_band(
        budget=budget,
        protein_min=target_ranges.protein_min,
    )

    if budget >= recommended_budget_min:
        return NegotiationResult(
            phase="planning",
            explanation="当前预算可以进入正式配餐。",
            recommended_budget_min=recommended_budget_min,
            recommended_budget_comfort=recommended_budget_comfort,
            options=[],
        )

    return NegotiationResult(
        phase="negotiating",
        explanation=(
            f"按你当前目标，{budget:.0f} 元更适合做折中方案。"
            f" 最低建议预算约 {recommended_budget_min:.0f} 元，"
            f" 更从容的预算约 {recommended_budget_comfort:.0f} 元。"
        ),
        recommended_budget_min=recommended_budget_min,
        recommended_budget_comfort=recommended_budget_comfort,
        options=[
            NegotiationOption(
                key="budget_cut",
                title="保守减脂",
                rationale="优先控热量和预算，蛋白尽量高但允许略低。",
                budget=budget,
                preferred_tags=["light"],
            ),
            NegotiationOption(
                key="protein_priority",
                title="高蛋白优先",
                rationale="优先保蛋白，价格更贴近预算上限。",
                budget=max(budget, min(recommended_budget_min, recommended_budget_comfort)),
                preferred_tags=["high_protein"],
            ),
        ],
    )
