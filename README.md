# Causal Uplift Experimentation Ops

Production-style causal ML system for A/B testing, uplift modeling, CATE estimation, targeting policy simulation, FastAPI serving, and monitoring.

## Goal

Estimate which users benefit from an intervention, not just which users are likely to convert.

## Milestone 1: synthetic experiment foundation

Milestone 1 provides a deterministic generator for a randomized user-level experiment. The
dataset contains customer covariates, a binary treatment assignment, conversion and spend
outcomes, and the known conversion-probability uplift used to simulate each user. Validation
utilities enforce the dataset schema, binary treatment and conversion values, non-negative
numeric spend, and complete required fields.

Install the project in editable mode:

```bash
python -m pip install -e .
```

Generate the default 10,000-row sample:

```bash
generate-synthetic-experiment
```

The command writes `data/processed/synthetic_experiment.csv`. The row count, seed, and output
path can be customized:

```bash
generate-synthetic-experiment --rows 5000 --seed 123 --output data/processed/experiment.csv
```

Run the quality checks:

```bash
python -m pytest
python -m ruff check .
```

## Milestone 2: baseline A/B experiment analysis

Milestone 2 adds treatment/control summaries, numeric covariate balance checks, conversion and
spend differences, relative conversion lift, a 95% confidence interval, and a two-sided
conversion-rate p-value. The analysis assumes randomized binary treatment, binary conversion,
and numeric spend. It estimates the average difference observed in the experiment; it does not
estimate individual treatment effects.

Generate the synthetic input data, then create the Markdown report:

```bash
generate-synthetic-experiment
generate-ab-report
```

The report is written to `reports/synthetic_ab_summary.md`. Custom paths are supported:

```bash
generate-ab-report --input data/processed/experiment.csv --output reports/ab_summary.md
```

Run all tests and lint checks:

```bash
python -m pytest
python -m ruff check .
```

## Milestone 3: uplift evaluation foundation

Milestone 3 adds a deterministic treatment-stratified train/test split, leakage-safe feature
metadata, uplift ranking tables, cumulative uplift and Qini-style curves, AUUC-style area, and
top-k targeting summaries. Synthetic `true_uplift` can be copied into an oracle score solely to
validate the evaluation protocol; it is explicitly excluded from model features.

Generate the data and both analysis reports:

```bash
generate-synthetic-experiment
generate-ab-report
generate-uplift-evaluation
```

The oracle evaluation report is written to `reports/synthetic_uplift_evaluation.md`. Its input,
output, split seed, test fraction, and number of ranking bins can be customized:

```bash
generate-uplift-evaluation --test-size 0.3 --seed 42 --bins 10
```

Run the complete test and lint suite:

```bash
python -m pytest
python -m ruff check .
```

## Milestone 4: logistic T-learner baseline

Milestone 4 adds the first fitted uplift baseline: separate logistic conversion models for treated
and control users. Numeric features are median-imputed and standardized; categorical features are
most-frequent-imputed and one-hot encoded with unknown-category handling. Predicted uplift is the
difference between the two predicted conversion probabilities, evaluated only on held-out rows.

Generate the data and all current reports:

```bash
generate-synthetic-experiment
generate-ab-report
generate-uplift-evaluation
generate-t-learner-report
```

The model report is written to `reports/synthetic_t_learner_report.md`. Split and report settings
can be customized:

```bash
generate-t-learner-report --test-size 0.3 --seed 42 --bins 10
```

Run the full test and lint suite:

```bash
python -m pytest
python -m ruff check .
```

## Milestone 5: repeated-split robustness

Milestone 5 reruns the same leakage-safe logistic T-learner over multiple deterministic,
treatment-stratified splits. It reports per-seed AUUC, Qini-style performance, maximum Qini gain,
and top-k uplift, then summarizes their mean, population standard deviation, minimum, maximum,
and positive-Qini frequency. No new model family is introduced.

Generate the data and all current reports:

```bash
generate-synthetic-experiment
generate-ab-report
generate-uplift-evaluation
generate-t-learner-report
generate-t-learner-robustness
```

The robustness report is written to `reports/t_learner_repeated_split_robustness.md`. Seeds and
test fraction can be customized:

```bash
generate-t-learner-robustness --seeds 0 1 2 3 4 --test-size 0.3
```

Run the full test and lint suite:

```bash
python -m pytest
python -m ruff check .
```

## Milestone 6: bootstrap uncertainty

Milestone 6 fits the existing T-learner on one fixed split, then resamples its scored test rows
within treatment arms. It reports percentile uncertainty for AUUC, Qini-style performance,
maximum Qini gain, and top-k uplift. These intervals capture held-out evaluation-sample
uncertainty; repeated-split robustness remains the diagnostic for training and split sensitivity.

Generate the data and all current reports:

```bash
generate-synthetic-experiment
generate-ab-report
generate-uplift-evaluation
generate-t-learner-report
generate-t-learner-robustness
generate-t-learner-bootstrap
```

The bootstrap report is written to `reports/t_learner_bootstrap_uncertainty.md`. Sample count and
seeds can be customized:

```bash
generate-t-learner-bootstrap --n-bootstrap 100 --bootstrap-seed 42 --split-seed 42
```

Run the full test and lint suite:

```bash
python -m pytest
python -m ruff check .
```

## Milestone 7: cross-fitted model comparison

Milestone 7 adds deterministic, treatment-stratified out-of-fold scoring and a reusable uplift
model registry. It compares logistic T- and S-learners, a random-forest T-learner, a deterministic
random-score baseline, and the synthetic oracle. Every row is scored exactly once by a model that
did not train on that row. Existing AUUC, Qini, top-k, and bootstrap utilities are reused.

Generate the data and all current reports:

```bash
generate-synthetic-experiment
generate-ab-report
generate-uplift-evaluation
generate-t-learner-report
generate-t-learner-robustness
generate-t-learner-bootstrap
generate-crossfit-comparison
```

The comparison report is written to `reports/crossfit_model_comparison.md`. Fold count, seed, and
bootstrap count can be customized:

```bash
generate-crossfit-comparison --folds 5 --seed 42 --n-bootstrap 100
```

Run the full test and lint suite:

```bash
python -m pytest
python -m ruff check .
```

## Milestone 8: targeting-policy simulation

Milestone 8 converts cross-fitted uplift rankings into offline business decisions. It compares
fixed-depth, positive-uplift, matched-random, and synthetic-oracle policies under configurable
conversion value, treatment cost, budget, capacity, and minimum-uplift assumptions. Incremental
value is estimated from randomized outcomes within each selected group.

Generate the data and all current reports:

```bash
generate-synthetic-experiment
generate-ab-report
generate-uplift-evaluation
generate-t-learner-report
generate-t-learner-robustness
generate-t-learner-bootstrap
generate-crossfit-comparison
generate-policy-simulation
```

The policy report is written to `reports/targeting_policy_simulation.md`. Economic and operational
constraints can be customized:

```bash
generate-policy-simulation --value-per-conversion 100 --treatment-cost 1 \
  --budget 5000 --capacity-fraction 0.3 --min-predicted-uplift 0
```

Run the full test and lint suite:

```bash
python -m pytest
python -m ruff check .
```

## Milestone 9: policy sensitivity analysis

Milestone 9 holds cross-fitted scores fixed while varying conversion value, treatment cost,
budget, and capacity. It reports one-way and two-way scenario results, recommendation stability,
learned-versus-random and learned-versus-oracle value, and deterministic policy break-even
thresholds.

Generate the data and all current reports:

```bash
generate-synthetic-experiment
generate-ab-report
generate-uplift-evaluation
generate-t-learner-report
generate-t-learner-robustness
generate-t-learner-bootstrap
generate-crossfit-comparison
generate-policy-simulation
generate-policy-sensitivity
```

The sensitivity report is written to `reports/policy_sensitivity_analysis.md`. Base assumptions
can be customized before applying the built-in sensitivity grids:

```bash
generate-policy-sensitivity --value-per-conversion 100 --treatment-cost 1 \
  --budget 5000 --capacity-fraction 0.3
```

Run the full test and lint suite:

```bash
python -m pytest
python -m ruff check .
```

## Milestone 10: policy value uncertainty

Milestone 10 applies a paired, treatment-stratified bootstrap to cross-fitted policy candidates.
It reports uncertainty for net value and ROI, probabilities of profitability and beating matched
random targeting, synthetic-oracle regret, and regret versus the best policy in each replicate.

Generate the data and all current reports:

```bash
generate-synthetic-experiment
generate-ab-report
generate-uplift-evaluation
generate-t-learner-report
generate-t-learner-robustness
generate-t-learner-bootstrap
generate-crossfit-comparison
generate-policy-simulation
generate-policy-sensitivity
generate-policy-uncertainty
```

The report is written to `reports/policy_value_uncertainty.md`. Bootstrap count and value
assumptions can be customized:

```bash
generate-policy-uncertainty --n-bootstrap 100 --value-per-conversion 100 \
  --treatment-cost 1 --folds 5 --seed 42
```

Run the full test and lint suite:

```bash
python -m pytest
python -m ruff check .
```

## Milestone 11: prospective randomized policy trial

Milestone 11 turns the selected offline policies into prospective randomized trial designs.
Cross-fitted Logistic S-learner scores define eligible users, who are newly randomized between
policy treatment and a holdout. The synthetic simulator samples new conversion outcomes from a
baseline probability plus known true uplift, then reports causal lift, confidence intervals,
economic value, guardrails, normal-approximation power planning, and cumulative operational
monitoring. The batch table is not presented as a formal sequential test.

Generate the data and all current reports:

```bash
generate-synthetic-experiment
generate-ab-report
generate-uplift-evaluation
generate-t-learner-report
generate-t-learner-robustness
generate-t-learner-bootstrap
generate-crossfit-comparison
generate-policy-simulation
generate-policy-sensitivity
generate-policy-uncertainty
generate-policy-trial
```

The prospective simulator report is written to `reports/prospective_policy_trial.md`. Trial
allocation, economics, planning targets, batches, and guardrails are configurable:

```bash
generate-policy-trial --holdout-fraction 0.2 --traffic-allocation 1 \
  --value-per-conversion 100 --treatment-cost 1 --mde-target 0.02 \
  --power 0.8 --batches 5 --minimum-sample-size 500
```

Run the full test and lint suite:

```bash
python -m pytest
python -m ruff check .
```
