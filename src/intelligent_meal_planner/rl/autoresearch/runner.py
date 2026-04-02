"""Experiment runner: train -> evaluate -> save artifact.

Orchestrates a single autoresearch experiment by training a DQN agent,
evaluating it against the benchmark, and saving a JSON summary.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Optional

import numpy as np
import torch

from intelligent_meal_planner.rl.autoresearch.benchmark import get_default_benchmark_cases
from intelligent_meal_planner.rl.autoresearch.evaluator import evaluate_agent, evaluate_agent_dual

# Required keys in the output summary.json
SUMMARY_REQUIRED_KEYS = [
    "run_id",
    "timesteps",
    "aggregate_score",
    "avg_reward",
    "calorie_error_pct",
    "budget_violation_rate",
    "diversity_score",
    "per_case",
    "timestamp",
]


def _train_and_get_agent(timesteps: int, checkpoint_dir: str, train_fn=None):
    """Train a DQN agent and return it for evaluation.

    This function is designed to be mockable in tests. When train_fn is
    provided (e.g. from dqn_train_config.py), it delegates to that function.
    Otherwise falls back to a built-in default training loop.

    Args:
        timesteps: Number of training timesteps.
        checkpoint_dir: Directory to save the checkpoint.
        train_fn: Optional callable(timesteps) -> agent. If provided, uses
            this instead of the built-in training loop.
    """
    if train_fn is not None:
        agent = train_fn(timesteps)
        ckpt_path = Path(checkpoint_dir) / "agent.pt"
        ckpt_path.parent.mkdir(parents=True, exist_ok=True)
        agent.save(str(ckpt_path))
        return agent

    # Default built-in training loop (backward compatible)
    from intelligent_meal_planner.rl.environment import MealPlanningEnv
    from intelligent_meal_planner.rl.dqn import MaskableDQNAgent

    config = {
        "hidden_dims": [256, 256, 128],
        "gamma": 0.99,
        "learning_rate": 1e-4,
        "learning_rate_end": 1e-5,
        "batch_size": 256,
        "train_freq": 4,
        "target_update_freq": 1000,
        "grad_clip": 10.0,
        "buffer_size": 100000,
        "min_buffer_size": min(10000, timesteps // 2),
        "epsilon_schedule": [
            (0, max(1, timesteps // 5), 1.0, 0.3),
            (max(1, timesteps // 5), max(2, timesteps * 3 // 5), 0.3, 0.1),
            (max(2, timesteps * 3 // 5), timesteps, 0.1, 0.02),
        ],
        "per_alpha": 0.6,
        "per_beta_start": 0.4,
        "per_beta_end": 1.0,
        "per_beta_steps": max(1, timesteps * 4 // 5),
        "n_envs": 8,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "total_timesteps": timesteps,
    }

    n_envs = config["n_envs"]
    envs = [MealPlanningEnv(training_mode=True) for _ in range(n_envs)]
    agent = MaskableDQNAgent(state_dim=13, action_dim=300, config=config)

    obs_list = [env.reset()[0] for env in envs]
    mask_list = [env.action_masks() for env in envs]

    global_step = 0
    while global_step < timesteps:
        for env in envs:
            env.global_step = global_step

        actions = [
            agent.select_action(obs_list[i], mask_list[i], global_step)
            for i in range(n_envs)
        ]

        for i in range(n_envs):
            next_obs, reward, terminated, truncated, info = envs[i].step(actions[i])
            done = terminated or truncated
            next_mask = envs[i].action_masks()

            agent.store_transition(
                obs_list[i], actions[i], reward, next_obs, done,
                mask_list[i], next_mask,
            )

            if done:
                obs_list[i], _ = envs[i].reset()
                mask_list[i] = envs[i].action_masks()
            else:
                obs_list[i] = next_obs
                mask_list[i] = next_mask

        global_step += n_envs

        if global_step % config["train_freq"] == 0:
            agent.train_step_fn()

    # Save checkpoint
    ckpt_path = Path(checkpoint_dir) / "agent.pt"
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    agent.save(str(ckpt_path))

    return agent


def run_experiment(
    run_id: str,
    timesteps: int,
    output_dir: str,
    description: str = "",
    price_scale: float = 1.0,
    budget_scale: float = 1.0,
    custom_recipes: Optional[list] = None,
) -> Dict[str, Any]:
    """Run a single autoresearch experiment: train, evaluate, save."""
    run_dir = Path(output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    agent = _train_and_get_agent(timesteps, str(run_dir / "checkpoints"))

    cases = get_default_benchmark_cases()
    eval_results = evaluate_agent_dual(
        agent, cases,
        price_scale=price_scale, budget_scale=budget_scale,
        custom_recipes=custom_recipes,
    )

    report = eval_results["report"]
    closed_per_case = eval_results["closed_result"]["per_case"]
    summary = {
        "run_id": run_id,
        "timesteps": timesteps,
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "aggregate_score": report["aggregate_score"],
        "closed_score": report.get("closed_score", report["aggregate_score"]),
        "open_score": report.get("open_score", report["aggregate_score"]),
        "avg_reward": report["avg_reward"],
        "calorie_error_pct": report["calorie_error_pct"],
        "budget_violation_rate": report["budget_violation_rate"],
        "diversity_score": report["diversity_score"],
        "per_case": closed_per_case,
    }

    summary_path = run_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    eval_results["per_case"] = closed_per_case
    return eval_results
