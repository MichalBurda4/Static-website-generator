.PHONY: help setup test lint format

help:
	@echo "make setup	- Install project dependencies and git hooks"
	@echo "make test 	- Run tests"
	@echo "make lint 	- Check the codebase with ruff and pyright"
	@echo "make format 	- Format the codebase with ruff"

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
