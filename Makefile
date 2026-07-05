PYTHON ?= python
PIP := $(PYTHON) -m pip

.PHONY: install test lint check generate-data reports artifact api-report observability smoke clean

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

check: test lint

generate-data:
	generate-synthetic-experiment --rows 10000 --seed 42

reports: generate-data
	generate-ab-report
	generate-uplift-evaluation
	generate-t-learner-report
	generate-t-learner-robustness
	generate-t-learner-bootstrap
	generate-crossfit-comparison
	generate-policy-simulation
	generate-policy-sensitivity
	generate-policy-uncertainty
	generate-policy-trial
	generate-experiment-planning

artifact: generate-data
	generate-policy-artifact

api-report: artifact
	generate-api-staging-report
	generate-api-safety-report

observability: artifact
	generate-api-audit-smoke-log
	generate-staging-observability

smoke:
	bash scripts/run_portfolio_smoke.sh

clean:
	rm -rf .pytest_cache .ruff_cache build dist data/processed
	rm -f artifacts/api_audit_log.jsonl
	rm -f artifacts/policy_bundle/model.joblib artifacts/policy_bundle/batch_scores.csv
	find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
	find src -maxdepth 1 -type d -name '*.egg-info' -exec rm -rf {} +
