SHELL := /bin/bash

.PHONY: all install lint format security secrets test ci clean run docker-build docker-run

# install depedecies
install:
	@echo "Installing dev dependencies..."
	uv pip install -r requirements-dev.txt

# Linting (flake8)
lint:
	@echo "Running flake8..."
	uv run flake8 .

# Formatting (black)
format:
	@echo "Running black..."
	uv run black .

# Security static analysis (bandit)
security:
	@echo "Running bandit..."
	uv run bandit -r . --exclude "./.venv,./build,./dist"

# Secrets scan (detect-secrets)
secrets:
	@echo "Running detect-secrets scan..."
	uv run detect-secrets scan --all-files

# Tests
test:
	@echo "Running pytest..."
	PYTHONPATH=. uv run pytest --maxfail=1 --disable-warnings -q


# Run everything (same order as your CI)
ci: install format lint security secrets test
	@echo "CI checks done."

# Remove caches/artifacts
clean:
	@echo "Cleaning pytest / python caches..."
	-rm -rf .pytest_cache __pycache__ .mypy_cache *.pyc *.pyo *~


