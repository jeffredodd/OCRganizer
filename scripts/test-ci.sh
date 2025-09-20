#!/bin/bash
# Test script to verify CI setup locally

set -e

echo "🧪 Testing CI setup locally..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "   Consider running: python -m venv venv && source venv/bin/activate"
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e .[dev]

# Run linting
echo "🔍 Running linters..."
echo "  - flake8..."
flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src tests --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

echo "  - black..."
black --check src tests

echo "  - isort..."
isort --check-only src tests

echo "  - mypy..."
mypy src --ignore-missing-imports

# Run tests
echo "🧪 Running tests..."
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Test version script
echo "📝 Testing version script..."
python scripts/version.py patch

echo "✅ All tests passed! CI setup is working correctly."
