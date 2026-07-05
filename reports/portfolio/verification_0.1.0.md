# Verification Transcript: 0.1.0

- Verification date: **2026-07-04**
- Local interpreter: **Python 3.13.11**
- Release version: **0.1.0**

This is a compact record of commands run against the release worktree. Long per-test progress
output is summarized, while command results and relevant status lines are preserved.

## Package version

```bash
causal-uplift-ops --version
```

```text
causal-uplift-ops 0.1.0
```

Result: exit code 0.

## Project information

```bash
causal-uplift-ops project-info
```

```text
Package: causal-uplift-experimentation-ops
Version: 0.1.0
Summary: Reproducible causal ML workflow for randomized experiments, uplift evaluation, treatment policy simulation, and staging operations.
Selected model: logistic_s_learner
Selected policy: all_positive_uplift
Artifact version: 1.0.0
Promotion status: hold
Key CLI commands:
  - generate-synthetic-experiment
  - generate-ab-report
  - generate-crossfit-comparison
  - generate-policy-artifact
  - score-policy-batch
  - serve-policy-api
  - generate-staging-observability
Limitations:
  - Model and policy validation use synthetic data only.
  - The FastAPI service is local/staging infrastructure, not a production deployment.
  - Artifact promotion is currently held pending real prospective randomized validation.
```

Result: exit code 0.

## Tests and lint through Make

```bash
make check
```

```text
collected 201 items
201 passed, 169 warnings in 30.42s
python -m ruff check .
All checks passed!
```

Result: exit code 0. The warnings are dependency deprecations from Starlette/httpx and
joblib/NumPy; no project test failed.

The direct commands were also run:

```bash
python -m pytest
python -m ruff check .
```

```text
201 passed, 169 warnings in 27.77s
All checks passed!
```

## Portfolio smoke workflow

```bash
bash scripts/run_portfolio_smoke.sh
```

The workflow regenerated the 10,000-row synthetic experiment, A/B report, cross-fitted model
comparison, frozen policy bundle, API report, deterministic audit fixture, and observability
report. Its final output was:

```text
Statuses: input=pass, prediction=warn, audit=pass, health=warn
Promotion decision: hold
201 passed, 169 warnings in 32.28s
All checks passed!
Portfolio smoke workflow completed successfully.
```

Result: exit code 0.

## Staging observability

```bash
generate-staging-observability
```

```text
Wrote staging observability report to reports/staging_observability_report.md
Statuses: input=pass, prediction=warn, audit=pass, health=warn
Promotion decision: hold
```

Result: exit code 0.

## Diff validation

```bash
git diff --check
```

Result: exit code 0 with no output.

## Docker availability

`docker info` was attempted. Docker Desktop reported that Docker was not available in this WSL 2
distribution and recommended enabling WSL integration. Therefore
`bash scripts/docker_smoke_test.sh` was not run locally. Dockerfile and smoke-script behavior are
covered by repository packaging checks, while an actual image build remains a release follow-up
on a host with a Docker daemon.
