# T-Learner Bootstrap Uncertainty

## Scope

This report fits the existing logistic T-learner once, then performs a treatment-stratified row
bootstrap on its fixed held-out prediction set. It measures evaluation-sample uncertainty, not
training or split-selection uncertainty.

- Dataset rows: 10,000
- Train rows: 7,000
- Test rows: 3,000
- Split seed: 42
- Bootstrap samples: 100
- Bootstrap seed: 42

## Base held-out metrics

| Metric | Value |
| --- | ---: |
| AUUC-style area | 0.019076 |
| Qini-style coefficient | 0.005076 |
| Maximum Qini gain | 0.013716 |
| Top 10% estimated uplift | 0.080000 |
| Top 20% estimated uplift | 0.063333 |
| Top 30% estimated uplift | 0.048889 |

## Bootstrap summary

| Metric | Mean | Std | 2.5% | 50% | 97.5% |
| --- | ---: | ---: | ---: | ---: | ---: |
| AUUC-style area | 0.018241 | 0.008569 | 0.000841 | 0.017161 | 0.034301 |
| Qini-style coefficient | 0.004584 | 0.003811 | -0.002425 | 0.004640 | 0.011660 |
| Maximum Qini gain | 0.015615 | 0.005516 | 0.005252 | 0.015534 | 0.024968 |
| Top 10% estimated uplift | 0.075067 | 0.057978 | -0.063833 | 0.080000 | 0.176833 |
| Top 20% estimated uplift | 0.059233 | 0.037880 | -0.020333 | 0.060000 | 0.133667 |
| Top 30% estimated uplift | 0.043644 | 0.028518 | -0.016722 | 0.042222 | 0.091111 |

## Approximate 95% percentile intervals

- AUUC-style area: [0.000841, 0.034301]
- Qini-style coefficient: [-0.002425, 0.011660]
- Positive Qini samples: 87 of 100
- Positive Qini rate: 87.0%

## Interpretation

The held-out uplift signal remains statistically uncertain because the bootstrap Qini interval includes zero. These percentile intervals condition on one fitted model and one test split; they do not include training-set or split-selection uncertainty.
