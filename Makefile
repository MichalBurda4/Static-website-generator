.PHONY: help setup test lint format build clean

# Show available make targets
help:
	@awk '/^#/{c=substr($$0,3);next}c&&/^[[:alpha:]][[:alnum:]_-]+:/{print substr($$1,1,index($$1,":")),c}1{c=0}' $(MAKEFILE_LIST) | column -s: -t

# Install project + git hooks
setup:
	uv sync
	uv run pre-commit install

# Run the test suite
test:
	uv run pytest --cov=ssg --cov-report=term-missing --cov-report=html:.artifacts/coverage/html

# Lint the codebase (ruff + pyright)
lint: 
	uv run ruff check --fix
	uv run pyright

# Auto-format Python sources with ruff
format: 
	uv run ruff format

# Build Markdown content into HTML under output/
build: 
	uv run ssg build

# View the output in the browser (locahost:8000)
view-output:
	uv run python -m http.server -d output -b localhost 8000

# View HTML tests coverage in the browser (localhost:8080)
view-coverage:
	uv run python -m http.server -d .artifacts/coverage/html -b localhost 8080

# Delete tool caches / coverage output
clean:
	rm -rf .artifacts
