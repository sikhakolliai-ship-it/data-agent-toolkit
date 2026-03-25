.PHONY: install test lint type-check deploy-dev deploy-prod eval fmt clean help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install all dependencies (dev + eval + guardrails)
	uv sync --all-extras

test:  ## Run unit tests with coverage
	uv run pytest tests/unit/ -v --cov=src/ --cov-report=term-missing

test-integration:  ## Run integration tests (requires Databricks cluster)
	uv run pytest tests/integration/ -v -m integration

test-all:  ## Run all tests including integration
	uv run pytest tests/ -v --cov=src/

lint:  ## Check code style with ruff
	uv run ruff check src/ tests/

fmt:  ## Auto-format code with ruff
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

type-check:  ## Run mypy type checking
	uv run mypy src/

eval:  ## Run agent quality evaluations (costs LLM tokens)
	uv run pytest tests/evaluation/ -v -m evaluation

deploy-dev:  ## Deploy bundle to dev workspace
	cd bundles && databricks bundle deploy -t dev

deploy-prod:  ## Deploy bundle to production workspace
	cd bundles && databricks bundle deploy -t prod

clean:  ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

ci: lint type-check test  ## Run full CI pipeline locally
