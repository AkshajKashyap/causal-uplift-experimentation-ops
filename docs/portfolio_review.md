# Portfolio Review Guide

## What this project demonstrates

- Designing and validating a deterministic randomized-experiment dataset
- Separating average A/B effects from heterogeneous treatment-effect ranking
- Preventing outcome, treatment, identifier, spend, and synthetic-truth leakage
- Comparing uplift baselines with cross-fitting, repeated splits, and bootstrap uncertainty
- Estimating policy value from randomized outcomes under cost, capacity, and budget assumptions
- Turning model evaluation into a pre-registered prospective validation plan
- Freezing a model, feature contract, economics, policy rule, fingerprints, and evidence paths
- Reusing one frozen scorer for batch decisions and FastAPI staging inference
- Adding staging authentication, auditability, budget controls, drift checks, and release gates
- Packaging the workflow behind CLIs, Make, Docker, tests, and CI

## What it does not demonstrate

This project does not demonstrate a treatment effect measured in a real population. It does not
provide observational causal identification, enterprise production infrastructure, cloud
deployment, a durable feature store, central treatment allocation, full security, or live
business monitoring. It also does not establish that the selected model or all-positive policy
will generalize beyond the simulator.

## How to discuss the synthetic-only limitation

Say it plainly: synthetic data makes the ground truth known and lets the evaluation, leakage,
uncertainty, and operational protocols be tested deterministically. It cannot establish external
validity, user impact, stable intervention delivery, or real incremental value.

The strongest part of the project is therefore not a headline uplift number. It is the chain of
evidence and controls that ends in a `hold` decision until a real randomized validation passes.
That is a more credible engineering and causal-inference story than presenting simulation results
as deployment approval.

## Best demo path

Run:

```bash
make install
make smoke
causal-uplift-ops project-info
```

Then review, in order:

1. `reports/synthetic_ab_summary.md` for the randomized baseline.
2. `reports/crossfit_model_comparison.md` for model-selection evidence.
3. `reports/targeting_policy_simulation.md` and `reports/policy_value_uncertainty.md` for decision
   economics.
4. `reports/experiment_preregistration.md` and `reports/prospective_policy_trial.md` for the
   proposed real validation.
5. `reports/policy_card.md` and `artifacts/policy_bundle/manifest.json` for the frozen contract.
6. `reports/api_staging_service.md` for serving behavior.
7. `reports/staging_observability_report.md` for drift, health, and the current `hold` gate.

If time is short, focus on the policy card, artifact manifest, and observability report. Together
they show how statistical evidence becomes a controlled operational decision.

## Strong interview talking points

- Why randomized policy value estimates are different from averaging predicted uplift
- Why uplift evaluation needs treatment-aware ranking metrics and out-of-fold predictions
- How leakage-safe feature metadata is carried from splitting through artifact serving
- Why repeated splits and bootstraps answer different uncertainty questions
- How economics can make broad treatment optimal even when ranking is imperfect
- Why a policy trial needs pre-specified efficacy, ROI, harm, and operational guardrails
- How dataset/config/file fingerprints improve auditability
- Why the API loads a frozen bundle instead of fitting at startup
- Why a technically healthy staging artifact can still receive a `hold` promotion decision
- How one CLI surface supports local use, CI, Make, and Docker without duplicating logic

## Honest weaknesses

- The data-generating process is simpler and cleaner than real customer behavior.
- The model set is intentionally small and classical.
- Confidence intervals and uplift metrics are transparent implementations rather than a
  standardized causal library.
- The all-positive policy yields a 100% recommendation rate under the configured economics,
  reducing the importance of ranking in the unconstrained case.
- API metrics and audit logs are process-local files without rotation or central aggregation.
- The Docker image prioritizes reviewability over minimal production image size.
- Dependency versions are not pinned in a lock file, so exact cross-platform byte reproduction is
  not guaranteed.

The next meaningful evidence is a real, pre-registered prospective randomized policy trial—not a
more elaborate synthetic model.
