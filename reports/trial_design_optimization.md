# Trial Design Optimization

## Planning assumptions

- Dataset rows per accumulated batch: 10,000
- Policies: Logistic S-learner / All positive uplift, Logistic S-learner / Top 20%
- Target absolute MDE for recommendations: 2.00%
- Target power: 80.0%
- Alpha: 0.050
- Holdout fractions evaluated: 10%, 20%, 30%, 40%, 50%
- Accumulated traffic multipliers evaluated: 1x, 2x, 3x, 5x, 10x
- Target MDE values evaluated: 1%, 2%, 3%, 5%

Power and MDE values are normal-approximation planning estimates. Rough expected value applies the
Milestone 11 simulated lift to future treated traffic; it is a planning assumption, not a promise.

## Policy planning inputs

| Policy | Eligible users per batch | Baseline conversion | Simulated lift assumption |
| --- | ---: | ---: | ---: |
| Logistic S-learner / All positive uplift | 10,000 | 11.20% | +4.36% |
| Logistic S-learner / Top 20% | 2,000 | 18.00% | +8.12% |

## Recommended adequately powered design by policy

The recommendation minimizes treatment cost among grid designs reaching target power for the
2-point lift. “Observed-lift multiplier” is the smallest grid multiplier powered for the larger
Milestone 11 simulated lift.

| Policy | Cheapest design (traffic / holdout) | Treatment / holdout N | Power | Cost | Rough net | Smallest target multiplier | Observed-lift multiplier | Highest-value design | Highest rough net | Current 1x/20% power |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic S-learner / All positive uplift | 1x / 50% | 5,000 / 5,000 | 86.4% | $5,000 | $+16,813 | 1x | 1x | 10x / 10% | $+302,625 | 70.5% |
| Logistic S-learner / Top 20% | 10x / 50% | 10,000 / 10,000 | 95.0% | $10,000 | $+71,250 | 10x | 1x | 10x / 20% | $+114,000 | 15.2% |

## Full scenario grid

| Policy | Target MDE | Holdout | Traffic | Eligible/batch | Treatment N | Holdout N | Design MDE | Power | Required N/group | Total N needed | Needed traffic | Status | Treatment cost | Rough net value |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| Logistic S-learner / All positive uplift | 1.0% | 10% | 1x | 10,000 | 9,000 | 1,000 | 2.95% | 15.8% | 15,613 | 87,406 | 9x | UNDERPOWERED | $9,000 | $+30,263 |
| Logistic S-learner / All positive uplift | 1.0% | 10% | 2x | 10,000 | 18,000 | 2,000 | 2.08% | 26.8% | 15,613 | 87,406 | 9x | UNDERPOWERED | $18,000 | $+60,525 |
| Logistic S-learner / All positive uplift | 1.0% | 10% | 3x | 10,000 | 27,000 | 3,000 | 1.70% | 37.5% | 15,613 | 87,406 | 9x | UNDERPOWERED | $27,000 | $+90,788 |
| Logistic S-learner / All positive uplift | 1.0% | 10% | 5x | 10,000 | 45,000 | 5,000 | 1.32% | 56.3% | 15,613 | 87,406 | 9x | UNDERPOWERED | $45,000 | $+151,313 |
| Logistic S-learner / All positive uplift | 1.0% | 10% | 10x | 10,000 | 90,000 | 10,000 | 0.93% | 85.0% | 15,613 | 87,406 | 9x | PASS | $90,000 | $+302,625 |
| Logistic S-learner / All positive uplift | 1.0% | 20% | 1x | 10,000 | 8,000 | 2,000 | 2.21% | 24.2% | 15,613 | 49,541 | 5x | UNDERPOWERED | $8,000 | $+26,900 |
| Logistic S-learner / All positive uplift | 1.0% | 20% | 2x | 10,000 | 16,000 | 4,000 | 1.56% | 42.9% | 15,613 | 49,541 | 5x | UNDERPOWERED | $16,000 | $+53,800 |
| Logistic S-learner / All positive uplift | 1.0% | 20% | 3x | 10,000 | 24,000 | 6,000 | 1.28% | 58.7% | 15,613 | 49,541 | 5x | UNDERPOWERED | $24,000 | $+80,700 |
| Logistic S-learner / All positive uplift | 1.0% | 20% | 5x | 10,000 | 40,000 | 10,000 | 0.99% | 80.4% | 15,613 | 49,541 | 5x | PASS | $40,000 | $+134,500 |
| Logistic S-learner / All positive uplift | 1.0% | 20% | 10x | 10,000 | 80,000 | 20,000 | 0.70% | 97.8% | 15,613 | 49,541 | 5x | PASS | $80,000 | $+269,000 |
| Logistic S-learner / All positive uplift | 1.0% | 30% | 1x | 10,000 | 7,000 | 3,000 | 1.93% | 30.1% | 15,613 | 38,032 | 4x | UNDERPOWERED | $7,000 | $+23,538 |
| Logistic S-learner / All positive uplift | 1.0% | 30% | 2x | 10,000 | 14,000 | 6,000 | 1.36% | 52.9% | 15,613 | 38,032 | 4x | UNDERPOWERED | $14,000 | $+47,075 |
| Logistic S-learner / All positive uplift | 1.0% | 30% | 3x | 10,000 | 21,000 | 9,000 | 1.11% | 70.1% | 15,613 | 38,032 | 4x | UNDERPOWERED | $21,000 | $+70,613 |
| Logistic S-learner / All positive uplift | 1.0% | 30% | 5x | 10,000 | 35,000 | 15,000 | 0.86% | 89.5% | 15,613 | 38,032 | 4x | PASS | $35,000 | $+117,688 |
| Logistic S-learner / All positive uplift | 1.0% | 30% | 10x | 10,000 | 70,000 | 30,000 | 0.61% | 99.5% | 15,613 | 38,032 | 4x | PASS | $70,000 | $+235,375 |
| Logistic S-learner / All positive uplift | 1.0% | 40% | 1x | 10,000 | 6,000 | 4,000 | 1.80% | 33.4% | 15,613 | 33,528 | 4x | UNDERPOWERED | $6,000 | $+20,175 |
| Logistic S-learner / All positive uplift | 1.0% | 40% | 2x | 10,000 | 12,000 | 8,000 | 1.28% | 58.1% | 15,613 | 33,528 | 4x | UNDERPOWERED | $12,000 | $+40,350 |
| Logistic S-learner / All positive uplift | 1.0% | 40% | 3x | 10,000 | 18,000 | 12,000 | 1.04% | 75.5% | 15,613 | 33,528 | 4x | UNDERPOWERED | $18,000 | $+60,525 |
| Logistic S-learner / All positive uplift | 1.0% | 40% | 5x | 10,000 | 30,000 | 20,000 | 0.81% | 92.8% | 15,613 | 33,528 | 4x | PASS | $30,000 | $+100,875 |
| Logistic S-learner / All positive uplift | 1.0% | 40% | 10x | 10,000 | 60,000 | 40,000 | 0.57% | 99.8% | 15,613 | 33,528 | 4x | PASS | $60,000 | $+201,750 |
| Logistic S-learner / All positive uplift | 1.0% | 50% | 1x | 10,000 | 5,000 | 5,000 | 1.77% | 34.3% | 15,613 | 32,428 | 4x | UNDERPOWERED | $5,000 | $+16,813 |
| Logistic S-learner / All positive uplift | 1.0% | 50% | 2x | 10,000 | 10,000 | 10,000 | 1.25% | 59.5% | 15,613 | 32,428 | 4x | UNDERPOWERED | $10,000 | $+33,625 |
| Logistic S-learner / All positive uplift | 1.0% | 50% | 3x | 10,000 | 15,000 | 15,000 | 1.02% | 76.9% | 15,613 | 32,428 | 4x | UNDERPOWERED | $15,000 | $+50,438 |
| Logistic S-learner / All positive uplift | 1.0% | 50% | 5x | 10,000 | 25,000 | 25,000 | 0.79% | 93.6% | 15,613 | 32,428 | 4x | PASS | $25,000 | $+84,063 |
| Logistic S-learner / All positive uplift | 1.0% | 50% | 10x | 10,000 | 50,000 | 50,000 | 0.56% | 99.8% | 15,613 | 32,428 | 4x | PASS | $50,000 | $+168,125 |
| Logistic S-learner / All positive uplift | 2.0% | 10% | 1x | 10,000 | 9,000 | 1,000 | 2.95% | 47.1% | 3,904 | 22,015 | 3x | UNDERPOWERED | $9,000 | $+30,263 |
| Logistic S-learner / All positive uplift | 2.0% | 10% | 2x | 10,000 | 18,000 | 2,000 | 2.08% | 76.1% | 3,904 | 22,015 | 3x | UNDERPOWERED | $18,000 | $+60,525 |
| Logistic S-learner / All positive uplift | 2.0% | 10% | 3x | 10,000 | 27,000 | 3,000 | 1.70% | 90.5% | 3,904 | 22,015 | 3x | PASS | $27,000 | $+90,788 |
| Logistic S-learner / All positive uplift | 2.0% | 10% | 5x | 10,000 | 45,000 | 5,000 | 1.32% | 98.8% | 3,904 | 22,015 | 3x | PASS | $45,000 | $+151,313 |
| Logistic S-learner / All positive uplift | 2.0% | 10% | 10x | 10,000 | 90,000 | 10,000 | 0.93% | 100.0% | 3,904 | 22,015 | 3x | PASS | $90,000 | $+302,625 |
| Logistic S-learner / All positive uplift | 2.0% | 20% | 1x | 10,000 | 8,000 | 2,000 | 2.21% | 70.5% | 3,904 | 12,568 | 2x | UNDERPOWERED | $8,000 | $+26,900 |
| Logistic S-learner / All positive uplift | 2.0% | 20% | 2x | 10,000 | 16,000 | 4,000 | 1.56% | 94.2% | 3,904 | 12,568 | 2x | PASS | $16,000 | $+53,800 |
| Logistic S-learner / All positive uplift | 2.0% | 20% | 3x | 10,000 | 24,000 | 6,000 | 1.28% | 99.1% | 3,904 | 12,568 | 2x | PASS | $24,000 | $+80,700 |
| Logistic S-learner / All positive uplift | 2.0% | 20% | 5x | 10,000 | 40,000 | 10,000 | 0.99% | 100.0% | 3,904 | 12,568 | 2x | PASS | $40,000 | $+134,500 |
| Logistic S-learner / All positive uplift | 2.0% | 20% | 10x | 10,000 | 80,000 | 20,000 | 0.70% | 100.0% | 3,904 | 12,568 | 2x | PASS | $80,000 | $+269,000 |
| Logistic S-learner / All positive uplift | 2.0% | 30% | 1x | 10,000 | 7,000 | 3,000 | 1.93% | 81.1% | 3,904 | 9,718 | 1x | PASS | $7,000 | $+23,538 |
| Logistic S-learner / All positive uplift | 2.0% | 30% | 2x | 10,000 | 14,000 | 6,000 | 1.36% | 98.0% | 3,904 | 9,718 | 1x | PASS | $14,000 | $+47,075 |
| Logistic S-learner / All positive uplift | 2.0% | 30% | 3x | 10,000 | 21,000 | 9,000 | 1.11% | 99.8% | 3,904 | 9,718 | 1x | PASS | $21,000 | $+70,613 |
| Logistic S-learner / All positive uplift | 2.0% | 30% | 5x | 10,000 | 35,000 | 15,000 | 0.86% | 100.0% | 3,904 | 9,718 | 1x | PASS | $35,000 | $+117,688 |
| Logistic S-learner / All positive uplift | 2.0% | 30% | 10x | 10,000 | 70,000 | 30,000 | 0.61% | 100.0% | 3,904 | 9,718 | 1x | PASS | $70,000 | $+235,375 |
| Logistic S-learner / All positive uplift | 2.0% | 40% | 1x | 10,000 | 6,000 | 4,000 | 1.80% | 85.5% | 3,904 | 8,627 | 1x | PASS | $6,000 | $+20,175 |
| Logistic S-learner / All positive uplift | 2.0% | 40% | 2x | 10,000 | 12,000 | 8,000 | 1.28% | 98.9% | 3,904 | 8,627 | 1x | PASS | $12,000 | $+40,350 |
| Logistic S-learner / All positive uplift | 2.0% | 40% | 3x | 10,000 | 18,000 | 12,000 | 1.04% | 99.9% | 3,904 | 8,627 | 1x | PASS | $18,000 | $+60,525 |
| Logistic S-learner / All positive uplift | 2.0% | 40% | 5x | 10,000 | 30,000 | 20,000 | 0.81% | 100.0% | 3,904 | 8,627 | 1x | PASS | $30,000 | $+100,875 |
| Logistic S-learner / All positive uplift | 2.0% | 40% | 10x | 10,000 | 60,000 | 40,000 | 0.57% | 100.0% | 3,904 | 8,627 | 1x | PASS | $60,000 | $+201,750 |
| Logistic S-learner / All positive uplift | 2.0% | 50% | 1x | 10,000 | 5,000 | 5,000 | 1.77% | 86.4% | 3,904 | 8,400 | 1x | PASS | $5,000 | $+16,813 |
| Logistic S-learner / All positive uplift | 2.0% | 50% | 2x | 10,000 | 10,000 | 10,000 | 1.25% | 99.1% | 3,904 | 8,400 | 1x | PASS | $10,000 | $+33,625 |
| Logistic S-learner / All positive uplift | 2.0% | 50% | 3x | 10,000 | 15,000 | 15,000 | 1.02% | 100.0% | 3,904 | 8,400 | 1x | PASS | $15,000 | $+50,438 |
| Logistic S-learner / All positive uplift | 2.0% | 50% | 5x | 10,000 | 25,000 | 25,000 | 0.79% | 100.0% | 3,904 | 8,400 | 1x | PASS | $25,000 | $+84,063 |
| Logistic S-learner / All positive uplift | 2.0% | 50% | 10x | 10,000 | 50,000 | 50,000 | 0.56% | 100.0% | 3,904 | 8,400 | 1x | PASS | $50,000 | $+168,125 |
| Logistic S-learner / All positive uplift | 3.0% | 10% | 1x | 10,000 | 9,000 | 1,000 | 2.95% | 80.6% | 1,735 | 9,855 | 1x | PASS | $9,000 | $+30,263 |
| Logistic S-learner / All positive uplift | 3.0% | 10% | 2x | 10,000 | 18,000 | 2,000 | 2.08% | 97.9% | 1,735 | 9,855 | 1x | PASS | $18,000 | $+60,525 |
| Logistic S-learner / All positive uplift | 3.0% | 10% | 3x | 10,000 | 27,000 | 3,000 | 1.70% | 99.8% | 1,735 | 9,855 | 1x | PASS | $27,000 | $+90,788 |
| Logistic S-learner / All positive uplift | 3.0% | 10% | 5x | 10,000 | 45,000 | 5,000 | 1.32% | 100.0% | 1,735 | 9,855 | 1x | PASS | $45,000 | $+151,313 |
| Logistic S-learner / All positive uplift | 3.0% | 10% | 10x | 10,000 | 90,000 | 10,000 | 0.93% | 100.0% | 1,735 | 9,855 | 1x | PASS | $90,000 | $+302,625 |
| Logistic S-learner / All positive uplift | 3.0% | 20% | 1x | 10,000 | 8,000 | 2,000 | 2.21% | 96.1% | 1,735 | 5,665 | 1x | PASS | $8,000 | $+26,900 |
| Logistic S-learner / All positive uplift | 3.0% | 20% | 2x | 10,000 | 16,000 | 4,000 | 1.56% | 100.0% | 1,735 | 5,665 | 1x | PASS | $16,000 | $+53,800 |
| Logistic S-learner / All positive uplift | 3.0% | 20% | 3x | 10,000 | 24,000 | 6,000 | 1.28% | 100.0% | 1,735 | 5,665 | 1x | PASS | $24,000 | $+80,700 |
| Logistic S-learner / All positive uplift | 3.0% | 20% | 5x | 10,000 | 40,000 | 10,000 | 0.99% | 100.0% | 1,735 | 5,665 | 1x | PASS | $40,000 | $+134,500 |
| Logistic S-learner / All positive uplift | 3.0% | 20% | 10x | 10,000 | 80,000 | 20,000 | 0.70% | 100.0% | 1,735 | 5,665 | 1x | PASS | $80,000 | $+269,000 |
| Logistic S-learner / All positive uplift | 3.0% | 30% | 1x | 10,000 | 7,000 | 3,000 | 1.93% | 98.8% | 1,735 | 4,409 | 1x | PASS | $7,000 | $+23,538 |
| Logistic S-learner / All positive uplift | 3.0% | 30% | 2x | 10,000 | 14,000 | 6,000 | 1.36% | 100.0% | 1,735 | 4,409 | 1x | PASS | $14,000 | $+47,075 |
| Logistic S-learner / All positive uplift | 3.0% | 30% | 3x | 10,000 | 21,000 | 9,000 | 1.11% | 100.0% | 1,735 | 4,409 | 1x | PASS | $21,000 | $+70,613 |
| Logistic S-learner / All positive uplift | 3.0% | 30% | 5x | 10,000 | 35,000 | 15,000 | 0.86% | 100.0% | 1,735 | 4,409 | 1x | PASS | $35,000 | $+117,688 |
| Logistic S-learner / All positive uplift | 3.0% | 30% | 10x | 10,000 | 70,000 | 30,000 | 0.61% | 100.0% | 1,735 | 4,409 | 1x | PASS | $70,000 | $+235,375 |
| Logistic S-learner / All positive uplift | 3.0% | 40% | 1x | 10,000 | 6,000 | 4,000 | 1.80% | 99.4% | 1,735 | 3,940 | 1x | PASS | $6,000 | $+20,175 |
| Logistic S-learner / All positive uplift | 3.0% | 40% | 2x | 10,000 | 12,000 | 8,000 | 1.28% | 100.0% | 1,735 | 3,940 | 1x | PASS | $12,000 | $+40,350 |
| Logistic S-learner / All positive uplift | 3.0% | 40% | 3x | 10,000 | 18,000 | 12,000 | 1.04% | 100.0% | 1,735 | 3,940 | 1x | PASS | $18,000 | $+60,525 |
| Logistic S-learner / All positive uplift | 3.0% | 40% | 5x | 10,000 | 30,000 | 20,000 | 0.81% | 100.0% | 1,735 | 3,940 | 1x | PASS | $30,000 | $+100,875 |
| Logistic S-learner / All positive uplift | 3.0% | 40% | 10x | 10,000 | 60,000 | 40,000 | 0.57% | 100.0% | 1,735 | 3,940 | 1x | PASS | $60,000 | $+201,750 |
| Logistic S-learner / All positive uplift | 3.0% | 50% | 1x | 10,000 | 5,000 | 5,000 | 1.77% | 99.5% | 1,735 | 3,860 | 1x | PASS | $5,000 | $+16,813 |
| Logistic S-learner / All positive uplift | 3.0% | 50% | 2x | 10,000 | 10,000 | 10,000 | 1.25% | 100.0% | 1,735 | 3,860 | 1x | PASS | $10,000 | $+33,625 |
| Logistic S-learner / All positive uplift | 3.0% | 50% | 3x | 10,000 | 15,000 | 15,000 | 1.02% | 100.0% | 1,735 | 3,860 | 1x | PASS | $15,000 | $+50,438 |
| Logistic S-learner / All positive uplift | 3.0% | 50% | 5x | 10,000 | 25,000 | 25,000 | 0.79% | 100.0% | 1,735 | 3,860 | 1x | PASS | $25,000 | $+84,063 |
| Logistic S-learner / All positive uplift | 3.0% | 50% | 10x | 10,000 | 50,000 | 50,000 | 0.56% | 100.0% | 1,735 | 3,860 | 1x | PASS | $50,000 | $+168,125 |
| Logistic S-learner / All positive uplift | 5.0% | 10% | 1x | 10,000 | 9,000 | 1,000 | 2.95% | 99.7% | 625 | 3,595 | 1x | PASS | $9,000 | $+30,263 |
| Logistic S-learner / All positive uplift | 5.0% | 10% | 2x | 10,000 | 18,000 | 2,000 | 2.08% | 100.0% | 625 | 3,595 | 1x | PASS | $18,000 | $+60,525 |
| Logistic S-learner / All positive uplift | 5.0% | 10% | 3x | 10,000 | 27,000 | 3,000 | 1.70% | 100.0% | 625 | 3,595 | 1x | PASS | $27,000 | $+90,788 |
| Logistic S-learner / All positive uplift | 5.0% | 10% | 5x | 10,000 | 45,000 | 5,000 | 1.32% | 100.0% | 625 | 3,595 | 1x | PASS | $45,000 | $+151,313 |
| Logistic S-learner / All positive uplift | 5.0% | 10% | 10x | 10,000 | 90,000 | 10,000 | 0.93% | 100.0% | 625 | 3,595 | 1x | PASS | $90,000 | $+302,625 |
| Logistic S-learner / All positive uplift | 5.0% | 20% | 1x | 10,000 | 8,000 | 2,000 | 2.21% | 100.0% | 625 | 2,093 | 1x | PASS | $8,000 | $+26,900 |
| Logistic S-learner / All positive uplift | 5.0% | 20% | 2x | 10,000 | 16,000 | 4,000 | 1.56% | 100.0% | 625 | 2,093 | 1x | PASS | $16,000 | $+53,800 |
| Logistic S-learner / All positive uplift | 5.0% | 20% | 3x | 10,000 | 24,000 | 6,000 | 1.28% | 100.0% | 625 | 2,093 | 1x | PASS | $24,000 | $+80,700 |
| Logistic S-learner / All positive uplift | 5.0% | 20% | 5x | 10,000 | 40,000 | 10,000 | 0.99% | 100.0% | 625 | 2,093 | 1x | PASS | $40,000 | $+134,500 |
| Logistic S-learner / All positive uplift | 5.0% | 20% | 10x | 10,000 | 80,000 | 20,000 | 0.70% | 100.0% | 625 | 2,093 | 1x | PASS | $80,000 | $+269,000 |
| Logistic S-learner / All positive uplift | 5.0% | 30% | 1x | 10,000 | 7,000 | 3,000 | 1.93% | 100.0% | 625 | 1,650 | 1x | PASS | $7,000 | $+23,538 |
| Logistic S-learner / All positive uplift | 5.0% | 30% | 2x | 10,000 | 14,000 | 6,000 | 1.36% | 100.0% | 625 | 1,650 | 1x | PASS | $14,000 | $+47,075 |
| Logistic S-learner / All positive uplift | 5.0% | 30% | 3x | 10,000 | 21,000 | 9,000 | 1.11% | 100.0% | 625 | 1,650 | 1x | PASS | $21,000 | $+70,613 |
| Logistic S-learner / All positive uplift | 5.0% | 30% | 5x | 10,000 | 35,000 | 15,000 | 0.86% | 100.0% | 625 | 1,650 | 1x | PASS | $35,000 | $+117,688 |
| Logistic S-learner / All positive uplift | 5.0% | 30% | 10x | 10,000 | 70,000 | 30,000 | 0.61% | 100.0% | 625 | 1,650 | 1x | PASS | $70,000 | $+235,375 |
| Logistic S-learner / All positive uplift | 5.0% | 40% | 1x | 10,000 | 6,000 | 4,000 | 1.80% | 100.0% | 625 | 1,492 | 1x | PASS | $6,000 | $+20,175 |
| Logistic S-learner / All positive uplift | 5.0% | 40% | 2x | 10,000 | 12,000 | 8,000 | 1.28% | 100.0% | 625 | 1,492 | 1x | PASS | $12,000 | $+40,350 |
| Logistic S-learner / All positive uplift | 5.0% | 40% | 3x | 10,000 | 18,000 | 12,000 | 1.04% | 100.0% | 625 | 1,492 | 1x | PASS | $18,000 | $+60,525 |
| Logistic S-learner / All positive uplift | 5.0% | 40% | 5x | 10,000 | 30,000 | 20,000 | 0.81% | 100.0% | 625 | 1,492 | 1x | PASS | $30,000 | $+100,875 |
| Logistic S-learner / All positive uplift | 5.0% | 40% | 10x | 10,000 | 60,000 | 40,000 | 0.57% | 100.0% | 625 | 1,492 | 1x | PASS | $60,000 | $+201,750 |
| Logistic S-learner / All positive uplift | 5.0% | 50% | 1x | 10,000 | 5,000 | 5,000 | 1.77% | 100.0% | 625 | 1,477 | 1x | PASS | $5,000 | $+16,813 |
| Logistic S-learner / All positive uplift | 5.0% | 50% | 2x | 10,000 | 10,000 | 10,000 | 1.25% | 100.0% | 625 | 1,477 | 1x | PASS | $10,000 | $+33,625 |
| Logistic S-learner / All positive uplift | 5.0% | 50% | 3x | 10,000 | 15,000 | 15,000 | 1.02% | 100.0% | 625 | 1,477 | 1x | PASS | $15,000 | $+50,438 |
| Logistic S-learner / All positive uplift | 5.0% | 50% | 5x | 10,000 | 25,000 | 25,000 | 0.79% | 100.0% | 625 | 1,477 | 1x | PASS | $25,000 | $+84,063 |
| Logistic S-learner / All positive uplift | 5.0% | 50% | 10x | 10,000 | 50,000 | 50,000 | 0.56% | 100.0% | 625 | 1,477 | 1x | PASS | $50,000 | $+168,125 |
| Logistic S-learner / Top 20% | 1.0% | 10% | 1x | 2,000 | 1,800 | 200 | 8.02% | 6.4% | 23,170 | 129,275 | 65x | UNDERPOWERED | $1,800 | $+12,825 |
| Logistic S-learner / Top 20% | 1.0% | 10% | 2x | 2,000 | 3,600 | 400 | 5.67% | 7.8% | 23,170 | 129,275 | 65x | UNDERPOWERED | $3,600 | $+25,650 |
| Logistic S-learner / Top 20% | 1.0% | 10% | 3x | 2,000 | 5,400 | 600 | 4.63% | 9.3% | 23,170 | 129,275 | 65x | UNDERPOWERED | $5,400 | $+38,475 |
| Logistic S-learner / Top 20% | 1.0% | 10% | 5x | 2,000 | 9,000 | 1,000 | 3.59% | 12.2% | 23,170 | 129,275 | 65x | UNDERPOWERED | $9,000 | $+64,125 |
| Logistic S-learner / Top 20% | 1.0% | 10% | 10x | 2,000 | 18,000 | 2,000 | 2.54% | 19.7% | 23,170 | 129,275 | 65x | UNDERPOWERED | $18,000 | $+128,250 |
| Logistic S-learner / Top 20% | 1.0% | 20% | 1x | 2,000 | 1,600 | 400 | 6.02% | 7.5% | 23,170 | 73,023 | 37x | UNDERPOWERED | $1,600 | $+11,400 |
| Logistic S-learner / Top 20% | 1.0% | 20% | 2x | 2,000 | 3,200 | 800 | 4.25% | 10.1% | 23,170 | 73,023 | 37x | UNDERPOWERED | $3,200 | $+22,800 |
| Logistic S-learner / Top 20% | 1.0% | 20% | 3x | 2,000 | 4,800 | 1,200 | 3.47% | 12.7% | 23,170 | 73,023 | 37x | UNDERPOWERED | $4,800 | $+34,200 |
| Logistic S-learner / Top 20% | 1.0% | 20% | 5x | 2,000 | 8,000 | 2,000 | 2.69% | 17.9% | 23,170 | 73,023 | 37x | UNDERPOWERED | $8,000 | $+57,000 |
| Logistic S-learner / Top 20% | 1.0% | 20% | 10x | 2,000 | 16,000 | 4,000 | 1.90% | 31.1% | 23,170 | 73,023 | 37x | UNDERPOWERED | $16,000 | $+114,000 |
| Logistic S-learner / Top 20% | 1.0% | 30% | 1x | 2,000 | 1,400 | 600 | 5.25% | 8.3% | 23,170 | 55,872 | 28x | UNDERPOWERED | $1,400 | $+9,975 |
| Logistic S-learner / Top 20% | 1.0% | 30% | 2x | 2,000 | 2,800 | 1,200 | 3.71% | 11.6% | 23,170 | 55,872 | 28x | UNDERPOWERED | $2,800 | $+19,950 |
| Logistic S-learner / Top 20% | 1.0% | 30% | 3x | 2,000 | 4,200 | 1,800 | 3.03% | 15.1% | 23,170 | 55,872 | 28x | UNDERPOWERED | $4,200 | $+29,925 |
| Logistic S-learner / Top 20% | 1.0% | 30% | 5x | 2,000 | 7,000 | 3,000 | 2.35% | 22.0% | 23,170 | 55,872 | 28x | UNDERPOWERED | $7,000 | $+49,875 |
| Logistic S-learner / Top 20% | 1.0% | 30% | 10x | 2,000 | 14,000 | 6,000 | 1.66% | 38.8% | 23,170 | 55,872 | 28x | UNDERPOWERED | $14,000 | $+99,750 |
| Logistic S-learner / Top 20% | 1.0% | 40% | 1x | 2,000 | 1,200 | 800 | 4.91% | 8.7% | 23,170 | 49,095 | 25x | UNDERPOWERED | $1,200 | $+8,550 |
| Logistic S-learner / Top 20% | 1.0% | 40% | 2x | 2,000 | 2,400 | 1,600 | 3.47% | 12.6% | 23,170 | 49,095 | 25x | UNDERPOWERED | $2,400 | $+17,100 |
| Logistic S-learner / Top 20% | 1.0% | 40% | 3x | 2,000 | 3,600 | 2,400 | 2.84% | 16.5% | 23,170 | 49,095 | 25x | UNDERPOWERED | $3,600 | $+25,650 |
| Logistic S-learner / Top 20% | 1.0% | 40% | 5x | 2,000 | 6,000 | 4,000 | 2.20% | 24.4% | 23,170 | 49,095 | 25x | UNDERPOWERED | $6,000 | $+42,750 |
| Logistic S-learner / Top 20% | 1.0% | 40% | 10x | 2,000 | 12,000 | 8,000 | 1.55% | 43.2% | 23,170 | 49,095 | 25x | UNDERPOWERED | $12,000 | $+85,500 |
| Logistic S-learner / Top 20% | 1.0% | 50% | 1x | 2,000 | 1,000 | 1,000 | 4.81% | 8.9% | 23,170 | 47,329 | 24x | UNDERPOWERED | $1,000 | $+7,125 |
| Logistic S-learner / Top 20% | 1.0% | 50% | 2x | 2,000 | 2,000 | 2,000 | 3.40% | 12.9% | 23,170 | 47,329 | 24x | UNDERPOWERED | $2,000 | $+14,250 |
| Logistic S-learner / Top 20% | 1.0% | 50% | 3x | 2,000 | 3,000 | 3,000 | 2.78% | 16.9% | 23,170 | 47,329 | 24x | UNDERPOWERED | $3,000 | $+21,375 |
| Logistic S-learner / Top 20% | 1.0% | 50% | 5x | 2,000 | 5,000 | 5,000 | 2.15% | 25.1% | 23,170 | 47,329 | 24x | UNDERPOWERED | $5,000 | $+35,625 |
| Logistic S-learner / Top 20% | 1.0% | 50% | 10x | 2,000 | 10,000 | 10,000 | 1.52% | 44.5% | 23,170 | 47,329 | 24x | UNDERPOWERED | $10,000 | $+71,250 |
| Logistic S-learner / Top 20% | 2.0% | 10% | 1x | 2,000 | 1,800 | 200 | 8.02% | 10.7% | 5,793 | 32,455 | 17x | UNDERPOWERED | $1,800 | $+12,825 |
| Logistic S-learner / Top 20% | 2.0% | 10% | 2x | 2,000 | 3,600 | 400 | 5.67% | 16.6% | 5,793 | 32,455 | 17x | UNDERPOWERED | $3,600 | $+25,650 |
| Logistic S-learner / Top 20% | 2.0% | 10% | 3x | 2,000 | 5,400 | 600 | 4.63% | 22.6% | 5,793 | 32,455 | 17x | UNDERPOWERED | $5,400 | $+38,475 |
| Logistic S-learner / Top 20% | 2.0% | 10% | 5x | 2,000 | 9,000 | 1,000 | 3.59% | 34.3% | 5,793 | 32,455 | 17x | UNDERPOWERED | $9,000 | $+64,125 |
| Logistic S-learner / Top 20% | 2.0% | 10% | 10x | 2,000 | 18,000 | 2,000 | 2.54% | 59.5% | 5,793 | 32,455 | 17x | UNDERPOWERED | $18,000 | $+128,250 |
| Logistic S-learner / Top 20% | 2.0% | 20% | 1x | 2,000 | 1,600 | 400 | 6.02% | 15.2% | 5,793 | 18,408 | 10x | UNDERPOWERED | $1,600 | $+11,400 |
| Logistic S-learner / Top 20% | 2.0% | 20% | 2x | 2,000 | 3,200 | 800 | 4.25% | 25.7% | 5,793 | 18,408 | 10x | UNDERPOWERED | $3,200 | $+22,800 |
| Logistic S-learner / Top 20% | 2.0% | 20% | 3x | 2,000 | 4,800 | 1,200 | 3.47% | 35.9% | 5,793 | 18,408 | 10x | UNDERPOWERED | $4,800 | $+34,200 |
| Logistic S-learner / Top 20% | 2.0% | 20% | 5x | 2,000 | 8,000 | 2,000 | 2.69% | 54.2% | 5,793 | 18,408 | 10x | UNDERPOWERED | $8,000 | $+57,000 |
| Logistic S-learner / Top 20% | 2.0% | 20% | 10x | 2,000 | 16,000 | 4,000 | 1.90% | 83.2% | 5,793 | 18,408 | 10x | PASS | $16,000 | $+114,000 |
| Logistic S-learner / Top 20% | 2.0% | 30% | 1x | 2,000 | 1,400 | 600 | 5.25% | 18.4% | 5,793 | 14,139 | 8x | UNDERPOWERED | $1,400 | $+9,975 |
| Logistic S-learner / Top 20% | 2.0% | 30% | 2x | 2,000 | 2,800 | 1,200 | 3.71% | 32.0% | 5,793 | 14,139 | 8x | UNDERPOWERED | $2,800 | $+19,950 |
| Logistic S-learner / Top 20% | 2.0% | 30% | 3x | 2,000 | 4,200 | 1,800 | 3.03% | 44.6% | 5,793 | 14,139 | 8x | UNDERPOWERED | $4,200 | $+29,925 |
| Logistic S-learner / Top 20% | 2.0% | 30% | 5x | 2,000 | 7,000 | 3,000 | 2.35% | 65.4% | 5,793 | 14,139 | 8x | UNDERPOWERED | $7,000 | $+49,875 |
| Logistic S-learner / Top 20% | 2.0% | 30% | 10x | 2,000 | 14,000 | 6,000 | 1.66% | 91.5% | 5,793 | 14,139 | 8x | PASS | $14,000 | $+99,750 |
| Logistic S-learner / Top 20% | 2.0% | 40% | 1x | 2,000 | 1,200 | 800 | 4.91% | 20.2% | 5,793 | 12,474 | 7x | UNDERPOWERED | $1,200 | $+8,550 |
| Logistic S-learner / Top 20% | 2.0% | 40% | 2x | 2,000 | 2,400 | 1,600 | 3.47% | 35.5% | 5,793 | 12,474 | 7x | UNDERPOWERED | $2,400 | $+17,100 |
| Logistic S-learner / Top 20% | 2.0% | 40% | 3x | 2,000 | 3,600 | 2,400 | 2.84% | 49.3% | 5,793 | 12,474 | 7x | UNDERPOWERED | $3,600 | $+25,650 |
| Logistic S-learner / Top 20% | 2.0% | 40% | 5x | 2,000 | 6,000 | 4,000 | 2.20% | 70.8% | 5,793 | 12,474 | 7x | UNDERPOWERED | $6,000 | $+42,750 |
| Logistic S-learner / Top 20% | 2.0% | 40% | 10x | 2,000 | 12,000 | 8,000 | 1.55% | 94.4% | 5,793 | 12,474 | 7x | PASS | $12,000 | $+85,500 |
| Logistic S-learner / Top 20% | 2.0% | 50% | 1x | 2,000 | 1,000 | 1,000 | 4.81% | 20.7% | 5,793 | 12,072 | 7x | UNDERPOWERED | $1,000 | $+7,125 |
| Logistic S-learner / Top 20% | 2.0% | 50% | 2x | 2,000 | 2,000 | 2,000 | 3.40% | 36.4% | 5,793 | 12,072 | 7x | UNDERPOWERED | $2,000 | $+14,250 |
| Logistic S-learner / Top 20% | 2.0% | 50% | 3x | 2,000 | 3,000 | 3,000 | 2.78% | 50.6% | 5,793 | 12,072 | 7x | UNDERPOWERED | $3,000 | $+21,375 |
| Logistic S-learner / Top 20% | 2.0% | 50% | 5x | 2,000 | 5,000 | 5,000 | 2.15% | 72.2% | 5,793 | 12,072 | 7x | UNDERPOWERED | $5,000 | $+35,625 |
| Logistic S-learner / Top 20% | 2.0% | 50% | 10x | 2,000 | 10,000 | 10,000 | 1.52% | 95.0% | 5,793 | 12,072 | 7x | PASS | $10,000 | $+71,250 |
| Logistic S-learner / Top 20% | 3.0% | 10% | 1x | 2,000 | 1,800 | 200 | 8.02% | 18.0% | 2,575 | 14,478 | 8x | UNDERPOWERED | $1,800 | $+12,825 |
| Logistic S-learner / Top 20% | 3.0% | 10% | 2x | 2,000 | 3,600 | 400 | 5.67% | 31.3% | 2,575 | 14,478 | 8x | UNDERPOWERED | $3,600 | $+25,650 |
| Logistic S-learner / Top 20% | 3.0% | 10% | 3x | 2,000 | 5,400 | 600 | 4.63% | 43.8% | 2,575 | 14,478 | 8x | UNDERPOWERED | $5,400 | $+38,475 |
| Logistic S-learner / Top 20% | 3.0% | 10% | 5x | 2,000 | 9,000 | 1,000 | 3.59% | 64.4% | 2,575 | 14,478 | 8x | UNDERPOWERED | $9,000 | $+64,125 |
| Logistic S-learner / Top 20% | 3.0% | 10% | 10x | 2,000 | 18,000 | 2,000 | 2.54% | 90.9% | 2,575 | 14,478 | 8x | PASS | $18,000 | $+128,250 |
| Logistic S-learner / Top 20% | 3.0% | 20% | 1x | 2,000 | 1,600 | 400 | 6.02% | 28.1% | 2,575 | 8,244 | 5x | UNDERPOWERED | $1,600 | $+11,400 |
| Logistic S-learner / Top 20% | 3.0% | 20% | 2x | 2,000 | 3,200 | 800 | 4.25% | 49.7% | 2,575 | 8,244 | 5x | UNDERPOWERED | $3,200 | $+22,800 |
| Logistic S-learner / Top 20% | 3.0% | 20% | 3x | 2,000 | 4,800 | 1,200 | 3.47% | 66.6% | 2,575 | 8,244 | 5x | UNDERPOWERED | $4,800 | $+34,200 |
| Logistic S-learner / Top 20% | 3.0% | 20% | 5x | 2,000 | 8,000 | 2,000 | 2.69% | 87.0% | 2,575 | 8,244 | 5x | PASS | $8,000 | $+57,000 |
| Logistic S-learner / Top 20% | 3.0% | 20% | 10x | 2,000 | 16,000 | 4,000 | 1.90% | 99.2% | 2,575 | 8,244 | 5x | PASS | $16,000 | $+114,000 |
| Logistic S-learner / Top 20% | 3.0% | 30% | 1x | 2,000 | 1,400 | 600 | 5.25% | 34.9% | 2,575 | 6,359 | 4x | UNDERPOWERED | $1,400 | $+9,975 |
| Logistic S-learner / Top 20% | 3.0% | 30% | 2x | 2,000 | 2,800 | 1,200 | 3.71% | 60.3% | 2,575 | 6,359 | 4x | UNDERPOWERED | $2,800 | $+19,950 |
| Logistic S-learner / Top 20% | 3.0% | 30% | 3x | 2,000 | 4,200 | 1,800 | 3.03% | 77.7% | 2,575 | 6,359 | 4x | UNDERPOWERED | $4,200 | $+29,925 |
| Logistic S-learner / Top 20% | 3.0% | 30% | 5x | 2,000 | 7,000 | 3,000 | 2.35% | 94.0% | 2,575 | 6,359 | 4x | PASS | $7,000 | $+49,875 |
| Logistic S-learner / Top 20% | 3.0% | 30% | 10x | 2,000 | 14,000 | 6,000 | 1.66% | 99.9% | 2,575 | 6,359 | 4x | PASS | $14,000 | $+99,750 |
| Logistic S-learner / Top 20% | 3.0% | 40% | 1x | 2,000 | 1,200 | 800 | 4.91% | 38.6% | 2,575 | 5,630 | 3x | UNDERPOWERED | $1,200 | $+8,550 |
| Logistic S-learner / Top 20% | 3.0% | 40% | 2x | 2,000 | 2,400 | 1,600 | 3.47% | 65.6% | 2,575 | 5,630 | 3x | UNDERPOWERED | $2,400 | $+17,100 |
| Logistic S-learner / Top 20% | 3.0% | 40% | 3x | 2,000 | 3,600 | 2,400 | 2.84% | 82.4% | 2,575 | 5,630 | 3x | PASS | $3,600 | $+25,650 |
| Logistic S-learner / Top 20% | 3.0% | 40% | 5x | 2,000 | 6,000 | 4,000 | 2.20% | 96.2% | 2,575 | 5,630 | 3x | PASS | $6,000 | $+42,750 |
| Logistic S-learner / Top 20% | 3.0% | 40% | 10x | 2,000 | 12,000 | 8,000 | 1.55% | 100.0% | 2,575 | 5,630 | 3x | PASS | $12,000 | $+85,500 |
| Logistic S-learner / Top 20% | 3.0% | 50% | 1x | 2,000 | 1,000 | 1,000 | 4.81% | 39.5% | 2,575 | 5,469 | 3x | UNDERPOWERED | $1,000 | $+7,125 |
| Logistic S-learner / Top 20% | 3.0% | 50% | 2x | 2,000 | 2,000 | 2,000 | 3.40% | 66.9% | 2,575 | 5,469 | 3x | UNDERPOWERED | $2,000 | $+14,250 |
| Logistic S-learner / Top 20% | 3.0% | 50% | 3x | 2,000 | 3,000 | 3,000 | 2.78% | 83.5% | 2,575 | 5,469 | 3x | PASS | $3,000 | $+21,375 |
| Logistic S-learner / Top 20% | 3.0% | 50% | 5x | 2,000 | 5,000 | 5,000 | 2.15% | 96.6% | 2,575 | 5,469 | 3x | PASS | $5,000 | $+35,625 |
| Logistic S-learner / Top 20% | 3.0% | 50% | 10x | 2,000 | 10,000 | 10,000 | 1.52% | 100.0% | 2,575 | 5,469 | 3x | PASS | $10,000 | $+71,250 |
| Logistic S-learner / Top 20% | 5.0% | 10% | 1x | 2,000 | 1,800 | 200 | 8.02% | 40.9% | 927 | 5,255 | 3x | UNDERPOWERED | $1,800 | $+12,825 |
| Logistic S-learner / Top 20% | 5.0% | 10% | 2x | 2,000 | 3,600 | 400 | 5.67% | 68.6% | 927 | 5,255 | 3x | UNDERPOWERED | $3,600 | $+25,650 |
| Logistic S-learner / Top 20% | 5.0% | 10% | 3x | 2,000 | 5,400 | 600 | 4.63% | 85.0% | 927 | 5,255 | 3x | PASS | $5,400 | $+38,475 |
| Logistic S-learner / Top 20% | 5.0% | 10% | 5x | 2,000 | 9,000 | 1,000 | 3.59% | 97.2% | 927 | 5,255 | 3x | PASS | $9,000 | $+64,125 |
| Logistic S-learner / Top 20% | 5.0% | 10% | 10x | 2,000 | 18,000 | 2,000 | 2.54% | 100.0% | 927 | 5,255 | 3x | PASS | $18,000 | $+128,250 |
| Logistic S-learner / Top 20% | 5.0% | 20% | 1x | 2,000 | 1,600 | 400 | 6.02% | 62.7% | 927 | 3,013 | 2x | UNDERPOWERED | $1,600 | $+11,400 |
| Logistic S-learner / Top 20% | 5.0% | 20% | 2x | 2,000 | 3,200 | 800 | 4.25% | 89.8% | 927 | 3,013 | 2x | PASS | $3,200 | $+22,800 |
| Logistic S-learner / Top 20% | 5.0% | 20% | 3x | 2,000 | 4,800 | 1,200 | 3.47% | 97.7% | 927 | 3,013 | 2x | PASS | $4,800 | $+34,200 |
| Logistic S-learner / Top 20% | 5.0% | 20% | 5x | 2,000 | 8,000 | 2,000 | 2.69% | 99.9% | 927 | 3,013 | 2x | PASS | $8,000 | $+57,000 |
| Logistic S-learner / Top 20% | 5.0% | 20% | 10x | 2,000 | 16,000 | 4,000 | 1.90% | 100.0% | 927 | 3,013 | 2x | PASS | $16,000 | $+114,000 |
| Logistic S-learner / Top 20% | 5.0% | 30% | 1x | 2,000 | 1,400 | 600 | 5.25% | 73.6% | 927 | 2,339 | 2x | UNDERPOWERED | $1,400 | $+9,975 |
| Logistic S-learner / Top 20% | 5.0% | 30% | 2x | 2,000 | 2,800 | 1,200 | 3.71% | 95.6% | 927 | 2,339 | 2x | PASS | $2,800 | $+19,950 |
| Logistic S-learner / Top 20% | 5.0% | 30% | 3x | 2,000 | 4,200 | 1,800 | 3.03% | 99.4% | 927 | 2,339 | 2x | PASS | $4,200 | $+29,925 |
| Logistic S-learner / Top 20% | 5.0% | 30% | 5x | 2,000 | 7,000 | 3,000 | 2.35% | 100.0% | 927 | 2,339 | 2x | PASS | $7,000 | $+49,875 |
| Logistic S-learner / Top 20% | 5.0% | 30% | 10x | 2,000 | 14,000 | 6,000 | 1.66% | 100.0% | 927 | 2,339 | 2x | PASS | $14,000 | $+99,750 |
| Logistic S-learner / Top 20% | 5.0% | 40% | 1x | 2,000 | 1,200 | 800 | 4.91% | 78.3% | 927 | 2,086 | 2x | UNDERPOWERED | $1,200 | $+8,550 |
| Logistic S-learner / Top 20% | 5.0% | 40% | 2x | 2,000 | 2,400 | 1,600 | 3.47% | 97.3% | 927 | 2,086 | 2x | PASS | $2,400 | $+17,100 |
| Logistic S-learner / Top 20% | 5.0% | 40% | 3x | 2,000 | 3,600 | 2,400 | 2.84% | 99.7% | 927 | 2,086 | 2x | PASS | $3,600 | $+25,650 |
| Logistic S-learner / Top 20% | 5.0% | 40% | 5x | 2,000 | 6,000 | 4,000 | 2.20% | 100.0% | 927 | 2,086 | 2x | PASS | $6,000 | $+42,750 |
| Logistic S-learner / Top 20% | 5.0% | 40% | 10x | 2,000 | 12,000 | 8,000 | 1.55% | 100.0% | 927 | 2,086 | 2x | PASS | $12,000 | $+85,500 |
| Logistic S-learner / Top 20% | 5.0% | 50% | 1x | 2,000 | 1,000 | 1,000 | 4.81% | 79.2% | 927 | 2,039 | 2x | UNDERPOWERED | $1,000 | $+7,125 |
| Logistic S-learner / Top 20% | 5.0% | 50% | 2x | 2,000 | 2,000 | 2,000 | 3.40% | 97.5% | 927 | 2,039 | 2x | PASS | $2,000 | $+14,250 |
| Logistic S-learner / Top 20% | 5.0% | 50% | 3x | 2,000 | 3,000 | 3,000 | 2.78% | 99.8% | 927 | 2,039 | 2x | PASS | $3,000 | $+21,375 |
| Logistic S-learner / Top 20% | 5.0% | 50% | 5x | 2,000 | 5,000 | 5,000 | 2.15% | 100.0% | 927 | 2,039 | 2x | PASS | $5,000 | $+35,625 |
| Logistic S-learner / Top 20% | 5.0% | 50% | 10x | 2,000 | 10,000 | 10,000 | 1.52% | 100.0% | 927 | 2,039 | 2x | PASS | $10,000 | $+71,250 |

## Optimization conclusions

- Cheapest adequately powered design: **Logistic S-learner / All positive uplift**, 1x traffic with 50% holdout ($5,000 treatment cost).
- Highest rough expected value among adequately powered designs: **Logistic S-learner / All positive uplift**, 10x traffic with 10% holdout ($+302,625 expected net value).
- Both Milestone 11 designs are underpowered for a 2-point lift.

Top-20% has the higher simulated lift and ROI, but only one fifth as many eligible users arrive per
batch, so confirming a small 2-point effect requires more accumulated traffic. All-positive has
more immediate sample size and lower treatment cost for a powered validation design, but treats
lower-ranked users and therefore has lower ROI.

Before serving, use the cheapest adequately powered all-positive design as the primary validation
trial under the current 2-point-MDE objective. Treat the top-20% policy as a separately powered
eligible-population trial; do not infer its efficacy from an underpowered one-batch comparison.
