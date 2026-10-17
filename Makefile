.PHONY: help setup test lint format

help:
	@echo "setup - Install project dependencies"
	@echo "test - Run tests"
	@echo "lint - Check the codebase with ruff and pyright"
	@echo "format - Format the codebase with ruff"

setup:
	uv run sync

test:
	uv run pytest

lint:
	uv run ruff check
	uv run pyright

format:
	uv run ruff format
