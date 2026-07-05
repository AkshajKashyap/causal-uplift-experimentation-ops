# Release Checklist: v0.1.0

## Quality and reproducibility

- [x] Full pytest suite passes: 201 tests
- [x] Ruff passes
- [x] Portfolio smoke workflow passes
- [x] GitHub Actions CI is configured for pushes and pull requests
- [x] CPU-only Python 3.12 Dockerfile is present
- [x] Main analysis and policy reports are generated
- [x] Policy card and artifact manifest are generated
- [x] Staging observability report is generated
- [x] README quickstart has been exercised locally

## Decision integrity

- [x] Promotion gate decision is documented as `hold`
- [x] Synthetic-only validation is documented prominently
- [x] The 100% recommendation-rate warning is documented
- [x] Real prospective randomized validation is named as the next required evidence
- [x] Simulated trial results are not presented as production impact

## Repository hygiene

- [x] Serialized model binaries are ignored
- [x] Generated batch scores and processed data are ignored
- [x] Local JSONL audit logs are ignored
- [x] Virtual environments, caches, coverage output, and build products are ignored
- [x] Local environment files, secrets, and private keys are ignored
- [x] Lightweight Markdown reports intended for review remain tracked
- [x] License, citation metadata, changelog, and contributing guide are present

## Release action

- [ ] Confirm the GitHub Actions run passes on the release commit
- [ ] Optionally run the Docker smoke test where a Docker daemon is available
- [ ] Create tag `v0.1.0`

Do not interpret this checklist as production approval. It only marks the repository as ready for
public portfolio review.
