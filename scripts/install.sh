#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${HOME}/.local/bin"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "🛡️  Installing skopos watcher..."

# Check Python version
if ! command -v "${PYTHON_BIN}" &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$("${PYTHON_BIN}" --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.9"

if ! "${PYTHON_BIN}" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "❌ Python ${REQUIRED_VERSION}+ required, found ${PYTHON_VERSION}"
    exit 1
fi

# Install package
echo "📦 Installing skopos package..."
"${PYTHON_BIN}" -m pip install --user --upgrade pip setuptools wheel
"${PYTHON_BIN}" -m pip install --user -e .

# Verify installation
if command -v skopos &> /dev/null; then
    echo "✅ skopos installed successfully!"
    echo ""
    skopos --version
    echo ""
    echo "Try: skopos scan"
else
    echo "⚠️  Installation complete but 'skopos' not in PATH."
    echo "   Add ${INSTALL_DIR} to your PATH or use: ${PYTHON_BIN} -m skopos.cli"
fi
