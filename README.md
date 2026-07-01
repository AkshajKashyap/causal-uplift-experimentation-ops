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
