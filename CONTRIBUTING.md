# Contributing

Thanks for helping improve this project. Contributions should preserve its central boundary:
transparent causal/uplift experimentation and staging operations without overstating synthetic
evidence.

## Development setup

```bash
git clone https://github.com/AkshajKashyap/causal-uplift-experimentation-ops.git
cd causal-uplift-experimentation-ops
python -m venv .venv
source .venv/bin/activate
make install
```

## Before opening a pull request

```bash
make check
bash scripts/run_portfolio_smoke.sh
git diff --check
```

Keep changes focused, deterministic, and readable. Add tests for behavior, prefer existing CLI and
scoring paths over duplicate implementations, and use explicit seeds for stochastic workflows.

## Generated artifacts

Large or local outputs such as processed data, serialized models, batch scores, and JSONL audit
logs are ignored. Lightweight Markdown evidence, policy configuration, and artifact manifests are
reviewable release material and may be updated when a workflow intentionally changes.

Never commit API keys, `.env` files, private data, local audit logs, or user-level scoring output.

## Causal and product claims

- Distinguish randomized estimates from model predictions.
- Do not describe synthetic validation as real-world causal evidence.
- Document economic assumptions and uncertainty when policy decisions change.
- Keep production deployment claims out of scope until a real prospective trial and operational
  review have passed.

## Pull-request notes

Summarize the problem, implementation, verification commands, generated report changes, and any
effect on the current promotion decision. A change that weakens leakage controls, reproducibility,
or the synthetic-only caveat needs explicit justification.
