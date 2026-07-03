# Policy Card: all_positive_uplift

## Frozen decision

- Artifact version: **1.0.0**
- Model: **logistic_s_learner**
- Policy: **all_positive_uplift**
- Decision rule: **predicted_uplift > 0**
- Created: 2026-07-03T06:26:59+00:00
- Random seed: 42
- Config fingerprint: `38cee44e01f2f092ba0eb179348fe3980381fc81fe49c45baf32d41121db5725`

## Intended use

Auditable offline batch scoring and prospective randomized policy validation.

## Out-of-scope use

Automated production treatment, high-stakes individual decisions, or use outside the documented population without new validation.

## Inputs and leakage controls

- Required features: `age`, `prior_purchases`, `avg_order_value`, `days_since_last_purchase`, `channel`
- Explicitly excluded identifiers, outcomes, treatment, and synthetic/debug fields: `conversion`, `predicted_control_conversion`, `predicted_treatment_conversion`, `predicted_uplift`, `spend`, `treatment`, `true_uplift`, `user_id`
- Missing numeric and categorical feature values use the fitted training-time preprocessing.
- Unknown categorical levels are ignored by the fitted one-hot encoder.

## Training data summary

- Rows: 10,000
- Columns: 10
- Dataset fingerprint: `543bdc505f595f138f9e4fe487723f4958cf0ec888c3d9321435c1ce52ad0a57`
- Content SHA-256: `6688baab7941f6867a1eaa0c9c367f4aeedcad2f4879061ea8ca114f8c38dba5`
- Validation scope: synthetic randomized experiment data only

## Value and capacity assumptions

- Value per conversion: $100.00
- Treatment cost per user: $1.00
- Capacity constraint: None
- Budget constraint: None

## Evaluation summary

Cross-fitted model comparison, randomized-data policy value estimation, and synthetic prospective
trial simulation support this frozen candidate. The all-positive choice maximizes total estimated
value under the current unconstrained economics; it is not evidence that ranking is irrelevant.

Evidence artifacts:
- `reports/crossfit_model_comparison.md`
- `reports/targeting_policy_simulation.md`
- `reports/policy_sensitivity_analysis.md`
- `reports/policy_value_uncertainty.md`
- `reports/prospective_policy_trial.md`
- `reports/trial_design_optimization.md`

## Uncertainty summary

The paired bootstrap report found positive value under the base synthetic assumptions, but
offline uncertainty cannot replace a prospective experiment. Because all-positive treats every
eligible user, a matched-random ranking comparison is not meaningful.

## Sensitivity summary

The selected policy is sensitive to conversion value, treatment cost, budget, and capacity.
All-positive winning with no constraints mostly reflects broad treatment profitability. Ranking
quality becomes materially more important under constrained treatment capacity or budget.

## Pre-registration and recommended validation trial

- Pre-registration: `reports/experiment_preregistration.md`
- Recommended trial: Before production serving, run the all-positive randomized validation at 1x accumulated traffic with a 50% holdout.
- Do not activate production treatment until the pre-registered randomized trial meets its
  efficacy, value, ROI, and guardrail decision rules.

## Known limitations

- The policy has been trained and evaluated only on synthetic data.
- Prospective real-world randomized validation is required before deployment.
- All-positive wins without budget or capacity constraints largely because broad treatment is profitable under the configured economics.
- Ranking quality matters more when treatment capacity or budget is constrained.
- Economic conclusions may change with treatment cost or conversion value.

## Ethical and business risks

- Broad treatment can impose user burden, fatigue, or unequal exposure even when average value is
  positive.
- Historical features and channel availability can proxy for access or demographic differences.
- Conversion value assumptions can prioritize short-term revenue over user welfare.
- Segment-level impact and treatment burden must be reviewed before launch.

## Operational risks

- Schema drift, unseen categories, stale features, duplicate users, or changed intervention cost
  can invalidate scores.
- A model artifact without matching configuration and fingerprints must not be used.
- Batch recommendations require idempotent delivery and auditable treatment logs.

## Deployment checklist

- [ ] Reproduce dataset and config fingerprints.
- [ ] Verify required input schema and batch row uniqueness.
- [ ] Freeze policy version, economics, eligibility rule, and randomization design.
- [ ] Run and analyze the pre-registered real-world randomized validation.
- [ ] Confirm all efficacy, value, ROI, fairness, and operational guardrails.
- [ ] Approve ownership, treatment logging, incident response, and rollback procedures.

## Rollback criteria

Disable recommendations if input validation fails, fingerprints do not match the approved bundle,
conversion lift or net value breaches a registered guardrail, treatment cost exceeds its limit,
material segment harm appears, or the delivered intervention differs from the frozen treatment
definition.
