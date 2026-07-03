# Prospective Randomized Policy Trial Simulation

## Scope

This is a synthetic prospective simulator. Cross-fitted Logistic S-learner scores define
eligibility, eligible users are newly randomized to policy treatment or holdout, and conversions
are newly sampled from a baseline probability plus known synthetic true uplift. It is not a
deployed experiment and does not establish production impact.

- Dataset rows: 10,000
- Policies: Logistic S-learner / All positive uplift, Logistic S-learner / Top 20%
- Cross-fitting folds: 5
- Traffic allocation to trial: 100.0%
- Holdout fraction among enrolled users: 20.0%
- Randomization seed: 42
- Value per conversion: $100.00
- Treatment cost per user: $1.00
- Alpha: 0.050
- Target power: 80.0%
- Target minimum detectable lift: 2.00%
- Operational monitoring batches: 5
- Guardrails: minimum sample 500, maximum treatment cost $10,000.00, minimum net value $0.00, minimum ROI +0.00, maximum negative lift 0.00%

## Final randomized trial estimates

Only policy-eligible, enrolled treatment and holdout users enter these estimates.

| Policy | Treatment | Holdout | Treatment conversion | Holdout conversion | Lift | 95% CI | P-value | Incremental conversions | Gross value | Treatment cost | Net value | ROI | Guardrails |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Logistic S-learner / All positive uplift | 8,000 | 2,000 | 15.56% | 11.20% | +4.36% | [+2.77%, +5.96%] | 0.0000 | +349.00 | $+34,900.00 | $8,000.00 | $+26,900.00 | +3.36 | PASS |
| Logistic S-learner / Top 20% | 1,600 | 400 | 26.12% | 18.00% | +8.12% | [+3.79%, +12.46%] | 0.0007 | +130.00 | $+13,000.00 | $1,600.00 | $+11,400.00 | +7.12 | PASS |

## MDE and power planning

Normal-approximation diagnostics use each policy's simulated holdout rate. Required sample size is
the approximate equal-sized count per group for the target lift.

| Policy | Baseline rate | Treatment N | Holdout N | Current-design MDE | Target lift | Required N/group | Approx. power at target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic S-learner / All positive uplift | 11.20% | 8,000 | 2,000 | 2.21% | 2.00% | 3,904 | 70.5% |
| Logistic S-learner / Top 20% | 18.00% | 1,600 | 400 | 6.02% | 2.00% | 5,793 | 15.2% |

## Guardrail checks

| Policy | Guardrail | Observed | Threshold | Status |
| --- | --- | ---: | --- | --- |
| Logistic S-learner / All positive uplift | minimum_sample_size | +10000.0000 | >= 500 | PASS |
| Logistic S-learner / All positive uplift | minimum_net_value | +26900.0000 | >= 0.00 | PASS |
| Logistic S-learner / All positive uplift | minimum_roi | +3.3625 | >= 0.00 | PASS |
| Logistic S-learner / All positive uplift | maximum_treatment_cost | +8000.0000 | <= 10000.00 | PASS |
| Logistic S-learner / All positive uplift | maximum_negative_conversion_lift | +0.0436 | >= -0.0000 | PASS |
| Logistic S-learner / Top 20% | minimum_sample_size | +2000.0000 | >= 500 | PASS |
| Logistic S-learner / Top 20% | minimum_net_value | +11400.0000 | >= 0.00 | PASS |
| Logistic S-learner / Top 20% | minimum_roi | +7.1250 | >= 0.00 | PASS |
| Logistic S-learner / Top 20% | maximum_treatment_cost | +1600.0000 | <= 10000.00 | PASS |
| Logistic S-learner / Top 20% | maximum_negative_conversion_lift | +0.0812 | >= -0.0000 | PASS |

## Cumulative batch monitoring

This table is operational monitoring only. Repeatedly reading ordinary p-values does not create a
valid sequential stopping rule; formal early stopping would require a pre-specified sequential
design and adjusted error control.

| Policy | Batch | Cumulative N | Treatment | Holdout | Lift | 95% CI | P-value | Net value | ROI | Guardrails |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Logistic S-learner / All positive uplift | 1 | 2,000 | 1,600 | 400 | +3.38% | [-0.36%, +7.11%] | 0.0948 | $+3,800.00 | +2.38 | PASS |
| Logistic S-learner / All positive uplift | 2 | 4,000 | 3,200 | 800 | +4.41% | [+1.86%, +6.95%] | 0.0018 | $+10,900.00 | +3.41 | PASS |
| Logistic S-learner / All positive uplift | 3 | 6,000 | 4,800 | 1,200 | +4.92% | [+2.85%, +6.98%] | 0.0000 | $+18,800.00 | +3.92 | PASS |
| Logistic S-learner / All positive uplift | 4 | 8,000 | 6,400 | 1,600 | +4.91% | [+3.13%, +6.68%] | 0.0000 | $+25,000.00 | +3.91 | PASS |
| Logistic S-learner / All positive uplift | 5 | 10,000 | 8,000 | 2,000 | +4.36% | [+2.77%, +5.96%] | 0.0000 | $+26,900.00 | +3.36 | PASS |
| Logistic S-learner / Top 20% | 1 | 400 | 320 | 80 | +5.62% | [-4.57%, +15.82%] | 0.3034 | $+1,480.00 | +4.62 | FAIL |
| Logistic S-learner / Top 20% | 2 | 800 | 640 | 160 | +4.38% | [-2.74%, +11.49%] | 0.2473 | $+2,160.00 | +3.38 | PASS |
| Logistic S-learner / Top 20% | 3 | 1,200 | 960 | 240 | +8.44% | [+2.84%, +14.03%] | 0.0067 | $+7,140.00 | +7.44 | PASS |
| Logistic S-learner / Top 20% | 4 | 1,600 | 1,280 | 320 | +8.75% | [+3.97%, +13.53%] | 0.0011 | $+9,920.00 | +7.75 | PASS |
| Logistic S-learner / Top 20% | 5 | 2,000 | 1,600 | 400 | +8.12% | [+3.79%, +12.46%] | 0.0007 | $+11,400.00 | +7.12 | PASS |

## Interpretation and recommended next step

Logistic S-learner / All positive uplift produces the higher simulated total net value ($+26,900.00); Logistic S-learner / Top 20% produces the higher ROI (+7.12). Its confidence interval excludes zero at the configured alpha. These results come from synthetic potential outcomes and validate the trial workflow, not real deployment impact. Before serving, pre-register the primary estimand and guardrails, confirm traffic and power assumptions, then run this randomized holdout design prospectively.
