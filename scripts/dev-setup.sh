#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "🔧 Setting up skopos development environment..."

# Install dev dependencies
echo "📦 Installing development dependencies..."
"${PYTHON_BIN}" -m pip install --user --upgrade pip setuptools wheel
"${PYTHON_BIN}" -m pip install --user -e ".[dev]"

# Install pre-commit hooks
if command -v pre-commit &> /dev/null; then
    echo "🪝 Installing pre-commit hooks..."
    pre-commit install
fi

echo "✅ Development environment ready!"
echo ""
echo "Run tests: pytest"
echo "Format code: black src tests"
echo "Type check: mypy src"
echo "Lint: ruff check src tests"
