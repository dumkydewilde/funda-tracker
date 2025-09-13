# Development Commands

.PHONY: install test lint format check pre-commit-test

# Install development dependencies
install:
	uv sync --extra dev

# Run tests
test:
	uv run pytest -v

# Run linting
lint:
	uv run ruff check .

# Run formatting
format:
	uv run ruff format .

# Run both linting and formatting
check: lint format

# Test pre-commit hooks
pre-commit-test:
	uv run pre-commit run --all-files

# Install pre-commit hooks
pre-commit-install:
	uv run pre-commit install

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
