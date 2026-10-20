# Static Site Generator (SSG)

A simple static site generator written in Python — project for Advanced Python Programming.

## Team

- Michał Burda
- Michał Broś
- Paweł Froń

## Installation

```bash
make setup
```

## Project structure

```
APP/
├── config.yaml          # site configuration
├── content/             # Markdown files with front matter
├── templates/           # Jinja2 templates
├── static/              # CSS, images
├── output/              # generated site (`make build`)
├── artifacts/           # tooling artifacts (venv, pytest cache, coverage, ruff)
├── src/ssg/             # source code
└── tests/               # tests
```

Tooling artifacts are kept under `artifacts/` (not scattered in the repo root):

| Path | Contents |
|------|----------|
| `artifacts/venv` | virtual environment (`make setup`) |
| `artifacts/pytest` | pytest cache |
| `artifacts/coverage` | coverage data + HTML report |
| `artifacts/ruff` | ruff cache |

## Build the site

```bash
python -m ssg.cli build
```

Generated files land in `output/` (`index.html` + one HTML file per post).
Open `output/index.html` in a browser to preview.

## Status

Completed:

1. Project structure and configuration
2. Markdown + front matter parsing
3. HTML generation from Jinja2 templates
4. Homepage with post list + individual post pages

## Writing content

See [docs/writing-content.md](docs/writing-content.md) for front matter fields and Markdown → HTML syntax.

## Parser usage example

```python
from pathlib import Path
from ssg.config import load_config
from ssg.parser import parse_markdown_file

config = load_config(Path("config.yaml"))
page = parse_markdown_file(Path("content/hello.md"))

print(page.title)
print(page.html)
```

## Tests & coverage

```bash
make test
```

This runs pytest with coverage and prints the percentage in the terminal.
An HTML report is written to `artifacts/coverage/html/index.html`.
