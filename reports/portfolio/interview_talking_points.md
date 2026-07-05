# Interview Talking Points

## Strong discussion points

- Average treatment effect answers whether treatment works overall; uplift ranking addresses who
  appears to benefit most.
- Randomized outcomes estimate policy value; predicted uplift alone is not treated as realized
  causal impact.
- Leakage controls exclude treatment, conversion, spend, identifiers, synthetic truth, and prior
  prediction columns from model features.
- Cross-fitting gives every training row an out-of-fold score before ranking and policy analysis.
- Repeated splits measure model/split sensitivity, while bootstrap intervals measure evaluation
  sample uncertainty; they answer different questions.
- The logistic T-learner ranks best by fitted-model Qini, but the logistic S-learner/all-positive
  pair wins simulated total net value under unconstrained economics.
- All-positive matching the random policy's net value shows why broad treatment profitability is
  not evidence of useful ranking.
- The policy artifact freezes model, features, rule, economics, evidence paths, and fingerprints
  rather than persisting a model alone.
- Batch and API inference reuse the same frozen scorer, reducing training-serving divergence.
- A healthy artifact can still be held: technical checks do not replace real causal evidence.
- The observability layer treats extreme recommendation rates as warnings even when stable.
- The one-command smoke workflow proves packaging, analysis, artifact, API documentation,
  monitoring, tests, and lint through the public CLI surface.

## Honest limitations

1. The entire evidence base is synthetic, so external validity and real user impact are unknown.
2. The model family is deliberately small and classical rather than a comprehensive CATE survey.
3. The all-positive decision makes ranking less important under the default unconstrained
   economics and creates a 100% recommendation-rate warning.
4. API metrics, audit logs, and monitoring are local snapshots without durable central storage,
   alerting, or production SLOs.
5. Dependencies are not lockfile-pinned, so exact binary reproduction can vary across platforms.

## Likely questions and concise answers

### 1. Why not deploy if the simulated trial passes?

The simulator validates code and decision rules against known synthetic potential outcomes. It
cannot validate intervention delivery, population transport, behavioral response, or real harms.
The gate therefore remains `hold` pending a real randomized trial.

### 2. Why freeze the S-learner when the T-learner has better Qini?

They optimize different objectives. The T-learner is the stronger ranker, but under the configured
$100 conversion value, $1 treatment cost, and no capacity constraint, the S-learner/all-positive
pair has the highest learned-policy total net value. That choice is conditional on those
economics, not a universal model ranking.

### 3. How is leakage prevented?

Feature metadata is created before fitting, and an explicit exclusion contract removes treatment,
outcomes, spend, user identifiers, true uplift, and prediction columns. Tests assert that contract,
and the frozen artifact records the selected feature list.

### 4. What would you monitor after a real launch?

Input freshness and drift, prediction and recommendation distributions, treatment delivery,
budget/capacity use, errors and latency, randomized incremental outcomes, segment harm, and
artifact identity. The current project implements only local snapshot versions of part of that
stack.

### 5. What is the next engineering or causal step?

Run the pre-registered policy-vs-holdout trial with real eligibility and delivery logs. Only after
efficacy, net value, harm/fairness, and operational guardrails pass should production architecture
or broader model work be prioritized.
