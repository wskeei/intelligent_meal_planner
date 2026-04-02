"""Tests for autoresearch experiment runner."""

import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from intelligent_meal_planner.rl.autoresearch.runner import (
    run_experiment,
    SUMMARY_REQUIRED_KEYS,
)


class TestExperimentRunner:
    """Test experiment runner produces correct artifacts."""

    def test_run_experiment_writes_summary_json(self, tmp_path):
        """Validate CLI writes summary.json with expected keys."""
        run_id = "test_run_001"

        # Mock the training to avoid actual GPU training
        fake_agent = MagicMock()
        fake_agent.select_action.side_effect = lambda state, mask, step, deterministic: int(
            np.where(mask)[0][0]
        )

        with patch(
            "intelligent_meal_planner.rl.autoresearch.runner._train_and_get_agent",
            return_value=fake_agent,
        ):
            result = run_experiment(
                run_id=run_id,
                timesteps=100,
                output_dir=str(tmp_path),
            )

        summary_path = tmp_path / run_id / "summary.json"
        assert summary_path.exists(), f"summary.json not found at {summary_path}"

        with open(summary_path) as f:
            summary = json.load(f)

        for key in SUMMARY_REQUIRED_KEYS:
            assert key in summary, f"Missing required key: {key}"

    def test_run_experiment_returns_report(self, tmp_path):
        """Validate the returned result includes the report."""
        fake_agent = MagicMock()
        fake_agent.select_action.side_effect = lambda state, mask, step, deterministic: int(
            np.where(mask)[0][0]
        )

        with patch(
            "intelligent_meal_planner.rl.autoresearch.runner._train_and_get_agent",
            return_value=fake_agent,
        ):
            result = run_experiment(
                run_id="test_run_002",
                timesteps=100,
                output_dir=str(tmp_path),
            )

        assert "report" in result
        assert "aggregate_score" in result["report"]
        assert "per_case" in result

    def test_summary_json_has_run_metadata(self, tmp_path):
        """Validate summary includes run_id and timesteps."""
        fake_agent = MagicMock()
        fake_agent.select_action.side_effect = lambda state, mask, step, deterministic: int(
            np.where(mask)[0][0]
        )

        with patch(
            "intelligent_meal_planner.rl.autoresearch.runner._train_and_get_agent",
            return_value=fake_agent,
        ):
            run_experiment(
                run_id="test_meta",
                timesteps=200,
                output_dir=str(tmp_path),
            )

        with open(tmp_path / "test_meta" / "summary.json") as f:
            summary = json.load(f)

        assert summary["run_id"] == "test_meta"
        assert summary["timesteps"] == 200
