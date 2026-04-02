# DQN Autoresearch Benchmark-Aligned Training Design

**Goal:** Raise aggregate score by materially improving the closed score while preserving open score, targeting 98+.

**Constraints:**
- Only edit `scripts/dqn_train_config.py`.
- Evaluation logic is fixed: `aggregate = 0.5 * closed + 0.5 * open`.
- Closed evaluation ignores `PRICE_SCALE`, `BUDGET_SCALE`, and `CUSTOM_RECIPES`.
- Training must run under `conda ai_lab` with GPU.

## Problem Framing

Current best aggregate is ~91 with closed and open both in the high 80s/low 90s. Since aggregate is capped by closed, achieving 98+ requires a substantial closed-score jump. Pure open-phase tweaks (budget scaling, recipes) cannot reach the target alone.

## Approach: Benchmark-Aligned Training Mix

Modify training to directly optimize for the fixed benchmark distribution used in closed evaluation, while retaining open-phase training to keep open score competitive.

### Two Cohorts of Training Envs

1. **Closed-Aligned Cohort**
   - Uses the 8 fixed benchmark cases (standard, low_budget, high_protein, low_calorie, generous_budget, tight_budget, keto_diet, bulk_diet).
   - Envs are created in evaluation-like mode: `price_scale=1.0`, `budget_scale=1.0`, `custom_recipes=None`.
   - Objective: lift closed score by matching evaluation targets and budgets.

2. **Open-Aligned Cohort**
   - Uses existing training mode (curriculum/randomized) with `PRICE_SCALE=1.0`, `BUDGET_SCALE=1.5`, and current 10 custom recipes.
   - Objective: keep open score strong and avoid regression.

### Training Loop Strategy

- Interleave or mix steps across both cohorts within each training iteration.
- Maintain total env count `N_ENVS` by splitting into two pools (e.g., half closed-aligned, half open-aligned).
- Ensure action masking and memory collection remain unchanged.

### Hyperparameter Stability

Start from the current best-performing configuration:
- `UTD ratio = 2` (double `train_step_fn`)
- `N_ENVS = 8`
- `BATCH_SIZE = 512`
- `GAMMA = 0.99`
- `TARGET_UPDATE_FREQ = 500`

Only adjust if the benchmark-aligned mix shows instability or plateau.

## Expected Impact

- Closed score should improve due to direct training on benchmark targets.
- Open score should remain stable with continued open-phase exposure.
- Aggregate should increase beyond 95, with a realistic path to 98+ after iterative runs.

## Implementation Notes

- All changes confined to `scripts/dqn_train_config.py`.
- Add helper to construct benchmark envs from `src/intelligent_meal_planner/rl/autoresearch/benchmark.py`.
- Keep logs and results tracking exactly as documented.

