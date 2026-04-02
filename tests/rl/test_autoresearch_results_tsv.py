"""Tests for autoresearch results TSV logging."""

import pytest
from pathlib import Path

from intelligent_meal_planner.rl.autoresearch.loop import (
    ensure_results_tsv,
    append_result_row,
    decide_keep_discard,
    RESULTS_HEADER,
)


class TestEnsureResultsTsv:
    """Test TSV header creation."""

    def test_creates_file_with_header(self, tmp_path):
        tsv_path = tmp_path / "results.tsv"
        ensure_results_tsv(str(tsv_path))
        assert tsv_path.exists()

        content = tsv_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 1  # header only
        assert lines[0] == RESULTS_HEADER

    def test_idempotent_on_existing_file(self, tmp_path):
        tsv_path = tmp_path / "results.tsv"
        ensure_results_tsv(str(tsv_path))
        ensure_results_tsv(str(tsv_path))  # second call

        content = tsv_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 1  # still just header


class TestAppendResultRow:
    """Test append row format."""

    def test_appends_tab_separated_row(self, tmp_path):
        tsv_path = tmp_path / "results.tsv"
        ensure_results_tsv(str(tsv_path))

        append_result_row(
            str(tsv_path),
            run_id="exp001",
            description="baseline test",
            aggregate_score=72.5,
            avg_reward=18.3,
            calorie_error_pct=12.1,
            budget_violation_rate=0.2,
            diversity_score=0.75,
            decision="keep",
        )

        content = tsv_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 2  # header + 1 row

        row = lines[1]
        fields = row.split("\t")
        assert fields[0] == "exp001"
        assert fields[1] == "baseline test"
        assert "," not in row  # no commas in row

    def test_multiple_appends(self, tmp_path):
        tsv_path = tmp_path / "results.tsv"
        ensure_results_tsv(str(tsv_path))

        for i in range(3):
            append_result_row(
                str(tsv_path),
                run_id=f"exp{i:03d}",
                description=f"run {i}",
                aggregate_score=70.0 + i,
                avg_reward=15.0 + i,
                calorie_error_pct=10.0 - i,
                budget_violation_rate=0.1,
                diversity_score=0.8,
                decision="keep" if i % 2 == 0 else "discard",
            )

        content = tsv_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 4  # header + 3 rows

    def test_no_commas_in_description(self, tmp_path):
        """Documented requirement: no commas in desc field."""
        tsv_path = tmp_path / "results.tsv"
        ensure_results_tsv(str(tsv_path))

        # Description with commas should have them stripped/replaced
        append_result_row(
            str(tsv_path),
            run_id="exp_comma",
            description="test, with, commas",
            aggregate_score=70.0,
            avg_reward=15.0,
            calorie_error_pct=10.0,
            budget_violation_rate=0.1,
            diversity_score=0.8,
            decision="keep",
        )

        content = tsv_path.read_text(encoding="utf-8")
        data_lines = content.strip().split("\n")[1:]
        for line in data_lines:
            assert "," not in line


class TestKeepDiscardLogic:
    """Test keep/discard threshold logic."""

    def test_keep_when_above_baseline(self):
        decision = decide_keep_discard(current_score=80.0, baseline_score=70.0)
        assert decision == "keep"

    def test_discard_when_below_baseline(self):
        decision = decide_keep_discard(current_score=60.0, baseline_score=70.0)
        assert decision == "discard"

    def test_keep_when_equal_to_baseline(self):
        decision = decide_keep_discard(current_score=70.0, baseline_score=70.0)
        assert decision == "keep"
