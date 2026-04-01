"""Autoresearch loop helpers: TSV logging and keep/discard logic.

Provides utilities for the outer research loop to log experiment results
in a machine-readable TSV format and make keep/discard decisions.
"""

from pathlib import Path

# Tab-separated header for results file
RESULTS_HEADER = "\t".join([
    "run_id",
    "description",
    "aggregate_score",
    "avg_reward",
    "calorie_error_pct",
    "budget_violation_rate",
    "diversity_score",
    "decision",
])


def ensure_results_tsv(path: str) -> None:
    """Create the results TSV file with header if it does not exist.

    Idempotent: does nothing if the file already exists.
    """
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
    avg_reward: float,
    calorie_error_pct: float,
    budget_violation_rate: float,
    diversity_score: float,
    decision: str,
) -> None:
    """Append one result row to the TSV file.

    Commas in the description are replaced with semicolons to satisfy
    the no-commas-in-row requirement.
    """
    # Sanitize description: replace commas
    description = description.replace(",", ";")

    fields = [
        run_id,
        description,
        f"{aggregate_score:.2f}",
        f"{avg_reward:.2f}",
        f"{calorie_error_pct:.1f}",
        f"{budget_violation_rate:.2f}",
        f"{diversity_score:.2f}",
        decision,
    ]
    row = "\t".join(fields)
    with open(path, "a", encoding="utf-8") as f:
        f.write(row + "\n")


def decide_keep_discard(current_score: float, baseline_score: float) -> str:
    """Decide whether to keep or discard an experiment result.

    Keep if the current score is >= the baseline score.

    Args:
        current_score: Aggregate score of the current experiment.
        baseline_score: Aggregate score to beat.

    Returns:
        "keep" or "discard".
    """
    return "keep" if current_score >= baseline_score else "discard"
