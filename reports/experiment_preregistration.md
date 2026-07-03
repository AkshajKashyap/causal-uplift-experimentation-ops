# Prospective uplift-policy randomized holdout trial

## Registration summary

- Model under test: **Logistic S-learner**
- Policy under test: **Logistic S-learner / All positive uplift**
- Registration status: **Planning artifact; freeze before enrollment**

## Motivation

Validate that acting on the cross-fitted uplift policy causes incremental conversion and economic value rather than merely looking favorable in offline analysis.

## Primary estimand and hypotheses

- Primary estimand: **Intent-to-treat conversion lift among policy-eligible users.**
- Null hypothesis: The eligible-population conversion rate is equal under policy treatment and holdout.
- Alternative hypothesis: The eligible-population conversion rate differs between policy treatment and holdout.
- Two-sided alpha: 0.050

## Treatment, control, and eligible population

- Treatment: Assignment to receive the intervention selected by the frozen candidate policy.
- Control/holdout: Assignment to the randomized policy holdout; no intervention is delivered.
- Eligible population: Users satisfying the frozen candidate policy rule before randomization.
- Randomization unit: User
- Analysis population: All randomized eligible users analyzed by assigned group (intent to treat).

### Exclusion rules

- Exclude users missing a stable identifier or required pre-treatment features.
- Exclude users already exposed to the intervention during the trial window.
- Apply exclusions before randomization and do not condition on post-treatment behavior.

## Outcomes

- Primary outcome: **Binary conversion during the pre-specified outcome window.**
- Secondary outcomes:
- net value
- ROI
- incremental conversions
- treatment cost

## Randomization plan

Randomize policy-eligible users to policy treatment or holdout using a reproducible assignment
mechanism. Preserve assignment regardless of receipt or compliance and analyze by original
assignment. The final holdout fraction and traffic duration must be frozen before enrollment.

## Sample-size and power plan

- Expected holdout conversion rate: 11.20%
- Target absolute MDE: 2.00%
- Target power: 80.0%
- Approximate equal-allocation requirement: **3,904 users per group**
- Approximate total under equal allocation: **7,808 users**

These are normal-approximation planning estimates. The final design must account for its actual
treatment/holdout allocation and should be selected from the design-optimization artifact.

## Guardrails

- minimum_sample_size: >= 500
- minimum_net_value: >= 0.00
- minimum_roi: >= 0.00
- maximum_treatment_cost: <= 10000.00
- maximum_negative_conversion_lift: >= -0.0000

## Decision rules

- Deploy only if conversion lift is positive and the two-sided p-value is below alpha.
- Require positive estimated net value and ROI at or above the configured minimum.
- Require every pre-specified guardrail to pass.
- If any deployment condition fails, do not deploy and investigate before a new test.

## Stopping rules

- Analyze the primary hypothesis after the pre-specified sample size or duration is met.
- Batch summaries are operational diagnostics, not unadjusted statistical stopping rules.
- Any safety stop must be documented independently of the efficacy decision.

## Analysis plan

- Estimate treatment-minus-holdout conversion rates among eligible randomized users.
- Report a two-sided confidence interval and p-value for the conversion-rate difference.
- Scale intent-to-treat lift by treated users for incremental conversions and value.
- Report treatment cost, net value, ROI, exclusions, and all guardrail outcomes.

## What this experiment can prove

Under successful randomization, adequate power, complete follow-up, and the frozen analysis plan,
the experiment can estimate whether assignment to this policy intervention caused incremental
conversion and economic value for the tested eligible population during the trial.

## What this experiment cannot prove

It cannot prove individual-level treatment effects, impact outside the eligible population,
permanent performance under drift, or value under different costs and conversion economics. It
also cannot turn synthetic simulator results into evidence of real-world impact.

## Limitations

- Normal-approximation power calculations are planning approximations.
- The trial identifies impact for the tested population, policy version, and intervention.
- A successful trial does not guarantee stability under future drift or changed economics.
- Synthetic simulations validate workflow behavior but are not production evidence.
