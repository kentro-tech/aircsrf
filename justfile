# Run the demo app
demo:
    uv run python tests/demo.py

# Run tests
test:
    uv run pytest

# Run tests with verbose output
test-v:
    uv run pytest -v

# Install dependencies
install:
    uv sync --all-extras

# Type check (if you add a type checker later)
check:
    uv run python -c "import air_csrf; print('Import OK')"
