.PHONY: install install-pipx test lint format typecheck build clean docs serve help

PYTHON ?= python3
PIP ?= pip

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install ai-bom with dev dependencies
	$(PIP) install -e ".[dev]"

install-all: ## Install ai-bom with all optional dependencies
	$(PIP) install -e ".[all,dev]"

install-pipx: ## Install ai-bom globally via pipx
	pipx install .

test: ## Run tests with coverage
	$(PYTHON) -m pytest -v --cov=ai_bom --cov-report=term-missing

test-fast: ## Run tests without coverage (faster)
	$(PYTHON) -m pytest -v -x

test-ci: ## Run tests with coverage and fail under threshold
	$(PYTHON) -m pytest -v --cov=ai_bom --cov-report=term-missing --cov-report=xml

lint: ## Run ruff linter
	ruff check src/ tests/

format: ## Format code with ruff
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck: ## Run mypy type checker
	mypy src/ai_bom/ --ignore-missing-imports

audit: ## Run pip-audit security check
	pip-audit

build: ## Build distribution packages
	$(PYTHON) -m build

clean: ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	rm -rf .ai-bom-cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docs: ## Build documentation site
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

demo: ## Run demo scan
	ai-bom scan examples/demo-project

scan-self: ## Scan this project for AI components
	ai-bom scan . --format table
