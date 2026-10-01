# Causal Memory Evaluation — One-Command Entry Point
# Protocol v0.2 (FROZEN)
#
# Usage:
#   make test          — Run all tests
#   make dev           — Run development experiment (mock model, no API)
#   make dev-analysis  — Run development analysis
#   make generate      — Regenerate benchmark v1 tasks
#   make protected     — Run protected experiment (REQUIRES AUTHORIZATION)
#   make clean         — Clean results directory

.PHONY: test dev dev-analysis generate protected clean

# Run all tests
test:
	python -m pytest tests -q

# Run development experiment (mock model, no API needed)
dev:
	python experiments/run_causal.py --config configs/causal_dev.yaml

# Run development analysis
dev-analysis:
	python experiments/analyze_causal.py --config configs/causal_dev.yaml

# Regenerate benchmark v1 tasks
generate:
	python experiments/generate_v1_benchmark.py

# Run protected experiment (REQUIRES EXPLICIT AUTHORIZATION)
# Requires .env with LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
# Requires authorization_approved: true in configs/causal_protected.yaml
protected:
	@if [ -f .env ]; then \
		echo "Found .env file"; \
	else \
		echo "ERROR: .env file not found. Create one with LLM_BASE_URL, LLM_API_KEY, LLM_MODEL"; \
		exit 1; \
	fi
	@echo "WARNING: This will run the PROTECTED comparison on HELD-OUT data."
	@echo "Ensure you have explicit authorization before proceeding."
	@read -p "Type 'AUTHORIZED' to proceed: " confirm; \
	if [ "$$confirm" != "AUTHORIZED" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	python experiments/run_causal.py --config configs/causal_protected.yaml

# Clean results directory
clean:
	rm -rf results/raw/* results/processed/*
	echo "Results directory cleaned."
