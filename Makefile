.PHONY: help setup test lint format

help:
	@echo "setup - Install project dependencies and git hooks"
	@echo "test - Run tests"
	@echo "lint - Check the codebase with ruff and pyright"
	@echo "format - Format the codebase with ruff"

setup:
	uv run sync
	uv run pre-commit install

test:
	uv run pytest

lint:
	uv run ruff check --fix
	uv run pyright

format:
	uv run ruff format
