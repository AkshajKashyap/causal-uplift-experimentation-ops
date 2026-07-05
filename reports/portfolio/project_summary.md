# Project Summary

## Problem

A conventional A/B test estimates whether an intervention works on average. A targeting decision
asks a harder question: which users are helped enough to justify treatment, under uncertainty,
cost, capacity, and operational constraints?

## Approach

This repository implements that decision chain on a deterministic synthetic randomized
experiment. Known simulation truth validates the evaluation protocol, while observed randomized
outcomes remain the basis for A/B and policy-value estimates. Outcome, treatment, spend,
identifiers, predicted fields, and synthetic truth are explicitly excluded from model features.

## System architecture

```text
seeded experiment -> A/B analysis -> cross-fitted uplift scores
                  -> policy economics and uncertainty
                  -> prospective trial plan and pre-registration
                  -> frozen model/policy artifact
                  -> batch scoring + FastAPI staging service
                  -> audit/drift/health checks -> promotion gate
```

Every layer is exposed through package CLIs and exercised by Make, CI, Docker support, and the
portfolio smoke workflow.

## Causal and uplift components

- Randomized treatment assignment and binary conversion outcomes
- Treatment/control effects, confidence intervals, p-values, and covariate balance
- Logistic T-learner, logistic S-learner, and random-forest T-learner
- Random-score and synthetic-oracle references
- Treatment-stratified splits and cross-fitted predictions
- AUUC/Qini-style curves, ranking tables, and top-k uplift
- Repeated-split and bootstrap uncertainty

The logistic T-learner is the strongest fitted ranker by Qini in the default cross-fitted report.
The frozen logistic S-learner is a different decision: paired with all-positive targeting, it
maximizes simulated total net value under the configured unconstrained economics.

## Experiment-design components

- Prospective policy-vs-holdout randomization
- Explicit estimands, alpha, power, MDE, traffic, and holdout assumptions
- Economic, sample-size, and negative-lift guardrails
- Pre-registration and trial-design optimization
- Honest separation between simulated trial validation and a real trial result

## Artifact, API, and monitoring components

- Persisted model, feature contract, policy rule, and value assumptions
- Dataset, feature, configuration, and file fingerprints
- Human-readable policy card and artifact manifest
- Shared scoring logic for batch and FastAPI inference
- Schema validation, optional API-key auth, request IDs, batch/cost limits, and structured errors
- Feature-free JSONL audit events and process-local metrics
- Numeric/categorical input drift, prediction drift, audit health, and evidence checks
- Deterministic `promote`, `hold`, or `rollback` gate

## Final decision status

The current staging artifact is **held**, not promoted. Input drift and audit health pass on the
local smoke snapshots, while prediction monitoring warns because all scores are positive and the
policy recommends treatment to the entire reference batch. More importantly, every causal and
economic result remains synthetic.

The system is ready for public code review and for designing a real prospective randomized
validation. It is not approved for production treatment delivery.
