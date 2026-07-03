# Policy Value Bootstrap Uncertainty

## Scope and assumptions

Cross-fitted scores are held fixed. Each paired bootstrap replicate resamples randomized treatment
arms, then evaluates every chosen policy on the same sampled users.

- Dataset rows: 10,000
- Cross-fitting folds: 5
- Bootstrap samples: 100
- Value per conversion: $100.00
- Treatment cost per user: $1.00
- Budget: None
- Capacity: None
- Policies evaluated: Logistic S-learner / All positive uplift, Logistic S-learner / Top 10%, Logistic S-learner / Top 20%, Logistic S-learner / Top 30%, Logistic T-learner / Top 20%, Random-forest T-learner / Top 20%, Random baseline / matched 20%, Synthetic oracle / matched 20%

## Policy net-value uncertainty

| Policy | Mean | Std | 2.5% | 50% | 97.5% | P(net > 0) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic S-learner / All positive uplift | $+30,038.00 | $6,557.60 | $+17,635.00 | $+30,300.00 | $+43,290.00 | 100.0% |
| Logistic S-learner / Top 10% | $+7,842.08 | $2,744.55 | $+2,332.80 | $+7,661.98 | $+12,668.97 | 100.0% |
| Logistic S-learner / Top 20% | $+13,023.62 | $3,876.43 | $+6,624.19 | $+12,745.22 | $+19,447.58 | 99.0% |
| Logistic S-learner / Top 30% | $+16,851.45 | $4,472.09 | $+7,001.79 | $+16,817.44 | $+24,612.44 | 100.0% |
| Logistic T-learner / Top 20% | $+14,198.14 | $4,031.08 | $+7,454.62 | $+14,700.59 | $+22,048.81 | 100.0% |
| Random-forest T-learner / Top 20% | $+9,091.68 | $3,327.78 | $+2,901.65 | $+8,649.02 | $+15,564.74 | 100.0% |
| Random baseline / Random matched to 20% | $+5,456.38 | $2,888.62 | $-247.03 | $+5,152.00 | $+11,072.74 | 97.0% |
| Synthetic oracle / Oracle matched to 20% | $+13,672.63 | $3,929.20 | $+6,536.31 | $+13,534.33 | $+21,333.93 | 100.0% |

## ROI uncertainty and paired comparisons

| Policy | Mean ROI | 2.5% | 50% | 97.5% | P(ROI > 0) | P(beats random) | P(beats all-positive) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic S-learner / All positive uplift | +3.00 | +1.76 | +3.03 | +4.33 | 100.0% | N/A | N/A |
| Logistic S-learner / Top 10% | +7.84 | +2.33 | +7.66 | +12.67 | 100.0% | 96.0% | 0.0% |
| Logistic S-learner / Top 20% | +6.51 | +3.31 | +6.37 | +9.72 | 99.0% | 97.0% | 0.0% |
| Logistic S-learner / Top 30% | +5.62 | +2.33 | +5.61 | +8.20 | 100.0% | 97.0% | 0.0% |
| Logistic T-learner / Top 20% | +7.10 | +3.73 | +7.35 | +11.02 | 100.0% | 98.0% | 0.0% |
| Random-forest T-learner / Top 20% | +4.55 | +1.45 | +4.32 | +7.78 | 100.0% | 86.0% | 0.0% |
| Random baseline / Random matched to 20% | +2.73 | -0.12 | +2.58 | +5.54 | 97.0% | N/A | N/A |
| Synthetic oracle / Oracle matched to 20% | +6.84 | +3.27 | +6.77 | +10.67 | 100.0% | N/A | N/A |

## Regret summary for learned policies

| Policy | Mean oracle regret | Median oracle regret | Oracle regret 95% interval | Mean best-policy regret | P(bootstrap-best) | P(beats random) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic S-learner / All positive uplift | $+0.00 | $+0.00 | [$+0.00, $+0.00] | $0.00 | 100.0% | N/A |
| Logistic S-learner / Top 10% | $+539.35 | $+464.68 | [$-3,149.74, $+5,780.40] | $22,195.92 | 0.0% | 96.0% |
| Logistic S-learner / Top 20% | $+649.01 | $+616.63 | [$-4,158.26, $+4,896.61] | $17,014.38 | 0.0% | 97.0% |
| Logistic S-learner / Top 30% | $+1,071.64 | $+832.46 | [$-4,359.27, $+6,267.04] | $13,186.55 | 0.0% | 97.0% |
| Logistic T-learner / Top 20% | $-525.52 | $-684.18 | [$-5,498.99, $+4,486.10] | $15,839.86 | 0.0% | 98.0% |
| Random-forest T-learner / Top 20% | $+4,580.95 | $+4,605.57 | [$-2,113.63, $+11,349.46] | $20,946.32 | 0.0% | 86.0% |

## Chosen-policy result

- Policy: **Logistic S-learner / All positive uplift**
- Mean net value: **$+30,038.00**
- Approximate 95% net-value interval: **[$+17,635.00, $+43,290.00]**
- Probability of positive net value: **100.0%**
- Probability of beating matched random: **N/A**
- Probability of being bootstrap-best: **100.0%**

## Interpretation

Under these fixed base assumptions, the all-positive policy remains justified for maximizing total net value. Its probability of positive net value is 100.0%. A matched-random comparison is not meaningful because both policies treat every user; their values tie by construction. Logistic S-learner / All positive uplift has the highest positive-value probability, while Logistic S-learner / All positive uplift is bootstrap-best most often. Constrained policies have higher ROI but lower total net value here. This conclusion remains fragile to the value, cost, and capacity assumptions explored in Milestone 9. Negative oracle regret can occur because realized randomized outcomes are noisy; true individual uplift is known only in this synthetic benchmark. Offline bootstrap uncertainty is not a substitute for a prospective production experiment.
