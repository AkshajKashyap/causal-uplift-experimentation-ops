# Architecture

## System boundary

This repository is a local, reproducible causal ML workflow. It covers randomized experiment
analysis through frozen-policy staging, but it deliberately stops before real treatment delivery
or cloud deployment. Data moves through explicit CSV, Markdown, JSON, JSONL, and joblib artifacts,
which keeps every stage inspectable.

## Workflow

```text
synthetic randomized data
        |
        v
A/B analysis and balance checks
        |
        v
leakage-safe uplift evaluation and model comparison
        |
        v
policy value, sensitivity, and uncertainty analysis
        |
        v
prospective trial planning and pre-registration
        |
        v
versioned model + policy artifact
        |
        +--> batch scoring
        |
        +--> FastAPI staging inference
                    |
                    v
          audit logs and offline observability
                    |
                    v
             promotion gate: hold
```

## Data generation

`causal_uplift_experimentation_ops.data` generates a deterministic randomized experiment from a
seed. Rows contain user covariates, binary treatment, conversion, spend, and a simulation-only
true uplift field. Validation enforces the schema, treatment and outcome domains, required values,
and reproducibility. Synthetic truth is useful for protocol testing but is excluded from fitted
model features.

## Experiment analysis

`experiments` calculates treatment/control summaries, covariate balance, conversion and spend
effects, confidence intervals, and p-values. These estimates rely on the randomized assignment;
the code does not extend the claim to observational data.

## Uplift modeling and evaluation

`models` contains simple leakage-safe baselines, while `evaluation` provides stratified splitting,
cross-fitting, ranking tables, AUUC- and Qini-style metrics, top-k policy summaries, repeated-split
robustness, and bootstrap uncertainty. The model registry keeps comparison code separate from
individual model implementations.

The selected frozen candidate is the logistic S-learner with the all-positive-uplift policy.
Selection is based on the documented synthetic evaluation and configured economics, not on a
claim of universal superiority.

## Policy simulation

`policy` converts uplift scores into treatment decisions and evaluates incremental conversions,
cost, value, ROI, budget/capacity constraints, sensitivity, uncertainty, and regret. Policy value
is estimated using randomized outcomes rather than treating model predictions as observed causal
effects.

## Trial planning

`experiments.policy_trial` simulates a prospective randomized validation of the frozen policy.
Planning utilities document traffic allocation, holdout design, power, MDE, economic thresholds,
and stopping or rollback guardrails. The generated pre-registration is evidence of a planned
decision process, not evidence that a real trial occurred.

## Artifact freezing

`artifacts` trains the selected model, freezes its feature contract and decision configuration,
persists the model, and writes a manifest. Dataset content, feature columns, configuration, and
artifact files receive deterministic fingerprints or hashes. Batch scoring loads this same
bundle, so offline and API decisions share one scoring implementation.

## API serving

`api` exposes health, version, policy, manifest, metrics, single-score, and batch-score endpoints.
The service loads an already-frozen artifact and never retrains. Pydantic schemas reject outcome,
treatment, and synthetic-truth leakage from request payloads.

## Safety controls

Staging controls include optional API-key authentication, request IDs, feature-free JSONL audit
events, batch limits, recommendation and treatment-cost guardrails, structured errors, and
process-local metrics. These controls are intentionally local: there is no enterprise identity,
central budget store, durable idempotency, distributed tracing, or high-availability design.

## Observability and promotion

`monitoring` compares reference and current feature distributions, summarizes prediction and
recommendation behavior, analyzes API audit events, checks artifact/report consistency, and
produces an operational health summary. Deterministic promotion gates return `promote`, `hold`, or
`rollback`.

The current artifact is held because all validation remains synthetic and the all-positive policy
produces a 100% recommendation-rate warning. This is the intended honest boundary: staging health
does not equal production approval.
