.PHONY: help install dev test lint format type-check security pip-compile clean examples check

PYTHON ?= python3
POETRY ?= poetry

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(POETRY) install --only main

dev: ## Install all dependencies (including dev)
	$(POETRY) install

test: ## Run tests
	$(POETRY) run pytest tests/ -v

lint: ## Run linters (ruff + black check)
	$(POETRY) run ruff check structured_address_fix/ tests/
	$(POETRY) run black --check structured_address_fix/ tests/

format: ## Auto-format code (ruff fix + black)
	$(POETRY) run ruff check --fix structured_address_fix/ tests/
	$(POETRY) run black structured_address_fix/ tests/

type-check: ## Run mypy type checking
	$(POETRY) run mypy structured_address_fix/

security: ## Run security scan (bandit)
	$(POETRY) run bandit -r structured_address_fix/ -c pyproject.toml 2>/dev/null || \
		$(POETRY) run bandit -r structured_address_fix/ -ll

pip-compile: ## Regenerate hash-pinned requirements/*.txt from requirements/*.in
	@command -v uv >/dev/null || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
	@for f in requirements/*.in; do \
		echo "compiling $$f"; \
		uv pip compile --quiet --generate-hashes --universal \
			--python-version 3.12 "$$f" -o "$${f%.in}.txt"; \
	done

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .eggs/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/
	rm -rf coverage.xml .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

examples: ## Verify example scripts run
	@for f in examples/*.py; do \
		[ -e "$$f" ] || { echo "no example scripts found"; break; }; \
		echo "running $$f"; \
		$(POETRY) run python "$$f" || exit 1; \
	done

check: lint type-check test ## Run all checks
