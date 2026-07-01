# Synthetic A/B Experiment Summary

## Scope

This report compares a randomized binary treatment against control. Conversion is binary and
spend is numeric. Estimates apply to this randomized experiment and do not imply individual
treatment effects.

## Sample

| Metric | Control | Treatment | Total |
| --- | ---: | ---: | ---: |
| Users | 5,000 | 5,000 | 10,000 |

## Outcomes

| Metric | Control | Treatment | Difference |
| --- | ---: | ---: | ---: |
| Conversion rate | 10.96% | 15.06% | +4.10 pp |
| Average spend | $9.89 | $13.87 | +$3.98 |

- Relative conversion lift: 37.41%
- 95% confidence interval for conversion-rate difference: [+2.78 pp, +5.42 pp]
- Two-sided p-value for conversion-rate difference: 1.103e-09

## Numeric covariate balance

Absolute standardized mean differences at or below 0.10 are marked balanced.

| Covariate | Control mean | Treatment mean | Standardized difference | Balanced |
| --- | ---: | ---: | ---: | :---: |
| age | 49.004 | 48.541 | -0.026 | Yes |
| prior_purchases | 3.016 | 3.011 | -0.003 | Yes |
| avg_order_value | 81.359 | 80.090 | -0.038 | Yes |
| days_since_last_purchase | 68.881 | 69.703 | 0.017 | Yes |

## Interpretation

Observed conversion increased under treatment by 4.10 percentage points. The two-sided p-value is below 0.05, providing evidence of a difference in conversion rates. All checked numeric covariates are within the 0.10 absolute standardized-difference threshold. These estimates describe the average effect in this randomized A/B experiment; they do not estimate individual uplift.
