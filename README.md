# Ztrade

[![CI](https://github.com/YOUR_USERNAME/ztrade/workflows/CI/badge.svg)](https://github.com/YOUR_USERNAME/ztrade/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project is an AI-powered trading company with autonomous trading agents.

## Quick Start

### Using uv (recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/YOUR_USERNAME/ztrade.git
cd ztrade

# Create virtual environment and install dependencies
uv sync

# Run the CLI
uv run ztrade hello
```

### Traditional setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the CLI
python cli/main.py hello
```

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black .

# Lint
uv run ruff check .

# Type check
uv run mypy cli/ mcp/
```

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation.