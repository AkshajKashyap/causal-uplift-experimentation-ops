# Release 0.1.0

- Version: **0.1.0**
- Release date: **2026-07-04**
- Repository purpose: reproducible synthetic causal ML experimentation and policy operations
- Promotion status: **hold**

## What the system does

The project starts with a seeded randomized experiment and carries the analysis through A/B
estimation, heterogeneous-effect ranking, treatment-policy economics, prospective trial planning,
artifact freezing, batch/API scoring, audit analysis, drift checks, and an explicit promotion
decision.

## Major capabilities

- Deterministic randomized data generation with known simulation truth
- A/B effects, confidence intervals, p-values, and covariate balance
- Leakage-safe uplift evaluation, cross-fitting, AUUC/Qini-style metrics, and uncertainty
- Multiple classical uplift baselines plus random and synthetic-oracle references
- Policy value, ROI, capacity, budget, sensitivity, bootstrap, and regret analysis
- Prospective randomized trial simulation, MDE/power planning, and pre-registration
- Versioned model/policy bundle, dataset/config/file fingerprints, and policy card
- FastAPI staging inference with safety controls and feature-free audit logs
- Offline drift, operational health, and deterministic promotion gates
- Make, Docker, CI, package metadata, tests, and one-command portfolio verification

## Verification

```bash
causal-uplift-ops --version
causal-uplift-ops project-info
python -m pytest
python -m ruff check .
make check
bash scripts/run_portfolio_smoke.sh
generate-staging-observability
git diff --check
```

The local release verification completed with **201 passing tests**, Ruff passing, the portfolio
smoke workflow passing, and a clean whitespace diff check. See
`reports/portfolio/verification_0.1.0.md` for the recorded command results.

## Limitations

- Every model, policy, and trial result uses synthetic data.
- The simulator cannot establish external validity or real user impact.
- The selected all-positive policy recommends treatment to 100% of the scored reference batch.
- Policy economics rely on configured conversion value and treatment cost.
- The API, audit log, metrics, and monitoring are local/staging implementations.
- Dependency versions are not locked for byte-identical cross-platform environments.

## Decision and next evidence

The frozen artifact is the logistic S-learner with an all-positive-uplift policy. It was selected
for simulated total net value under unconstrained economics, even though the logistic T-learner
ranks best among fitted models by Qini. The promotion gate correctly returns **hold** because the
evidence is synthetic-only; prediction monitoring also warns on the 100% recommendation and
positive-score rates.

The next real-world step is the pre-registered prospective randomized holdout trial. Production
treatment should remain disabled until efficacy, value, harm, fairness, and operational
guardrails pass on real data.
