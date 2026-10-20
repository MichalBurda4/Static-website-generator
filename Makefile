# Development tasks for the Static Site Generator.
# Run `make help` to list targets. Each target is described by the `#` comment above it.

ARTIFACTS := artifacts
export UV_PROJECT_ENVIRONMENT := $(ARTIFACTS)/venv

.PHONY: help setup test lint format build clean

# Show available make targets
help:
	@echo "make setup   - create venv in artifacts/ and install dependencies + hooks"
	@echo "make test    - run tests and show coverage percentage"
	@echo "make lint    - check code with ruff and pyright"
	@echo "make format  - format code with ruff"
	@echo "make build   - generate the static site into output/"
	@echo "make clean   - remove caches and coverage reports under artifacts/"

# Create the virtualenv under artifacts/venv and install project + git hooks
setup:
	uv sync
	uv run pre-commit install

# Run the test suite and print terminal + HTML coverage reports
test:
	uv run pytest --cov=ssg --cov-report=term-missing --cov-report=html:$(ARTIFACTS)/coverage/html

# Lint the codebase (ruff + pyright)
lint:
	uv run ruff check --fix
	uv run pyright

# Auto-format Python sources with ruff
format:
	uv run ruff format

# Build Markdown content into HTML under output/
build:
	uv run python -m ssg.cli build

# Delete tool caches / coverage output (does not remove the venv)
clean:
	uv run python -c "from pathlib import Path; import shutil; root=Path('$(ARTIFACTS)'); \
	[shutil.rmtree(p, ignore_errors=True) for p in [root/'pytest', root/'coverage', root/'ruff']]; \
	print('Cleaned pytest/coverage/ruff caches under artifacts/')"
