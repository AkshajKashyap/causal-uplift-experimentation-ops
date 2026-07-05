# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No unreleased changes.

## [0.1.0] - 2026-07-04

### Added

- Deterministic synthetic randomized-experiment generation and validation
- Baseline A/B analysis with balance, effect, confidence-interval, and p-value reporting
- Leakage-safe splitting, uplift ranking, AUUC/Qini-style metrics, and top-k policy evaluation
- Logistic T-learner, logistic S-learner, random-forest T-learner, random, and oracle comparison
- Repeated-split, bootstrap, and cross-fitted uncertainty evaluation
- Treatment-policy simulation with economic, budget, capacity, sensitivity, and regret analysis
- Prospective randomized-policy trial simulation, power planning, and pre-registration
- Versioned policy artifact, manifest fingerprints, policy card, and batch scoring
- FastAPI staging inference with validation, optional authentication, request IDs, audit logging,
  recommendation/cost guardrails, and process-local metrics
- Offline input/prediction drift, audit analysis, operational health, and promotion gates
- Package metadata CLI, Makefile, Docker support, GitHub Actions CI, and portfolio smoke workflow
- Architecture, reproducibility, portfolio-review, and release documentation

### Decision status

- Frozen candidate: logistic S-learner with the all-positive-uplift policy
- Promotion decision: **hold**
- Reason: synthetic-only evidence and an extreme 100% recommendation-rate warning
- Required next evidence: a real pre-registered prospective randomized validation

[Unreleased]: https://github.com/AkshajKashyap/causal-uplift-experimentation-ops/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/AkshajKashyap/causal-uplift-experimentation-ops/releases/tag/v0.1.0
