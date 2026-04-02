"""Autoresearch loop helpers: TSV logging and keep/discard logic."""

from pathlib import Path

RESULTS_HEADER = "\t".join([
    "run_id",
    "description",
    "aggregate_score",
    "closed_score",
    "open_score",
    "avg_reward",
    "calorie_error_pct",
    "budget_violation_rate",
    "diversity_score",
    "price_scale",
    "budget_scale",
    "n_custom_recipes",
    "decision",
])


def ensure_results_tsv(path: str) -> None:
    """Create the results TSV file with header if it does not exist."""
    p = Path(path)
    if p.exists():
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(RESULTS_HEADER + "\n", encoding="utf-8")


def append_result_row(
    path: str,
    *,
    run_id: str,
    description: str,
    aggregate_score: float,
    closed_score: float = 0.0,
    open_score: float = 0.0,
    avg_reward: float,
    calorie_error_pct: float,
    budget_violation_rate: float,
    diversity_score: float,
    price_scale: float = 1.0,
    budget_scale: float = 1.0,
    n_custom_recipes: int = 0,
    decision: str,
) -> None:
    """Append one result row to the TSV file."""
    description = description.replace(",", ";")
    fields = [
        run_id, description,
        f"{aggregate_score:.2f}", f"{closed_score:.2f}", f"{open_score:.2f}",
        f"{avg_reward:.2f}", f"{calorie_error_pct:.1f}",
        f"{budget_violation_rate:.2f}", f"{diversity_score:.2f}",
        f"{price_scale:.2f}", f"{budget_scale:.2f}",
        str(n_custom_recipes), decision,
    ]
    with open(path, "a", encoding="utf-8") as f:
        f.write("\t".join(fields) + "\n")


def decide_keep_discard(current_score: float, baseline_score: float) -> str:
    """Keep if current score >= baseline."""
    return "keep" if current_score >= baseline_score else "discard"
