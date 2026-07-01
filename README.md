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
