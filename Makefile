# Makefile for OCRganizer

.PHONY: help install install-dev test test-cov lint format clean build docs

# Default target
help:
	@echo "OCRganizer Development Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  lint         Run linting (flake8, mypy)"
	@echo "  format       Format code (black, isort)"
	@echo "  clean        Clean up build artifacts"
	@echo ""
	@echo "Application:"
	@echo "  run-web      Start web interface"
	@echo "  run-cli      Run CLI with sample data"
	@echo ""
	@echo "Build:"
	@echo "  build        Build distribution packages"
	@echo "  docs         Generate documentation"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e .[dev]

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

test-integration:
	pytest tests/test_e2e_integration.py -v -m integration

# Code quality
lint:
	flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/ *.py
	isort src/ tests/ *.py

format-check:
	black --check src/ tests/ *.py
	isort --check-only src/ tests/ *.py

# Application
run-web:
	python app.py

run-cli:
	python cli.py --dry-run --verbose

run-cli-sample:
	python cli.py --input input_pdfs --output output --dry-run

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Build
build: clean
	python -m build

# Development environment
setup-dev: install-dev
	pre-commit install

# Docker (if needed)
docker-build:
	docker build -t pdf-categorizer .

docker-run:
	docker run -p 5000:5000 -v $(PWD)/input_pdfs:/app/input_pdfs -v $(PWD)/output:/app/output pdf-categorizer

# Documentation
docs:
	@echo "Generating API documentation..."
	@mkdir -p docs/
	@echo "# API Documentation" > docs/api.md
	@echo "Generated on $$(date)" >> docs/api.md

# Utility targets
check-env:
	@echo "Checking environment configuration..."
	@python -c "from src.config import get_config; c = get_config(); print(f'AI Provider: {c.ai.preferred_provider}'); print(f'Input Dir: {c.files.input_dir}'); print(f'Output Dir: {c.files.output_dir}')"

list-deps:
	pip list --format=freeze

# CI/CD helpers
ci-test: format-check lint test-cov

# Quick development cycle
dev: format lint test

# Full quality check
quality: format-check lint test-cov
