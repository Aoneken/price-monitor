.PHONY: help install install-dev test test-unit test-integration coverage lint format clean webapp cli db-reset

PYTHON := .venv/bin/python
PIP := .venv/bin/pip

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Setup
install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -r requirements-dev.txt

venv: ## Create virtual environment
	python3 -m venv .venv
	@echo "✓ Virtual environment created. Activate with: source .venv/bin/activate"

# Testing
test: ## Run all tests
	$(PYTHON) -m pytest tests/ -v

test-unit: ## Run unit tests only
	$(PYTHON) -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	$(PYTHON) -m pytest tests/integration/ -v

test-watch: ## Run tests in watch mode
	$(PYTHON) -m pytest tests/ -v -f

coverage: ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ --cov=price_monitor --cov=webapp --cov-report=term-missing --cov-report=html
	@echo "✓ Coverage report generated in htmlcov/index.html"

# Code Quality
lint: ## Run linting checks
	$(PYTHON) -m flake8 price_monitor webapp tests

lint-mypy: ## Run type checking
	$(PYTHON) -m mypy price_monitor webapp --ignore-missing-imports

format: ## Format code with black and isort
	$(PYTHON) -m isort price_monitor webapp tests scripts
	$(PYTHON) -m black price_monitor webapp tests scripts

check: lint lint-mypy ## Run all checks

# Application
webapp: ## Start web application
	$(PYTHON) run_webapp.py

cli: ## Run CLI scraper (interactive)
	@read -p "Start date (YYYY-MM-DD): " start; \
	read -p "End date (YYYY-MM-DD): " end; \
	read -p "Guests: " guests; \
	read -p "Selector: " selector; \
	$(PYTHON) -m price_monitor.cli.main --start $$start --end $$end --guests $$guests --select "$$selector"

# Database
db-reset: ## Reset database
	rm -f price_monitor.db
	$(PYTHON) -c 'from webapp.database import init_db; init_db(); print("✓ Database reset")'

# Maintenance
clean: ## Clean generated files
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache htmlcov .coverage .mypy_cache
	@echo "✓ Cleaned"

clean-all: clean ## Clean everything including database and logs
	rm -f price_monitor.db
	rm -f logs/*.log
	@echo "✓ Deep clean complete"
