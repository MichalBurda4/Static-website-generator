# Static Site Generator (SSG)

A simple static site generator written in Python — project for Advanced Python Programming.

## Team

- Michał Burda
- Michał Broś
- Paweł Froń

## Installation

```bash
pip install -e ".[dev]"
```

## Project structure

```
APP/
├── config.yaml          # site configuration
├── content/             # Markdown files with front matter
├── templates/           # Jinja2 templates (next stage)
├── static/              # CSS, images
├── output/              # generated site (next stage)
├── src/ssg/             # source code
└── tests/               # tests
```

## Status

Completed:

1. Project structure and configuration
2. Markdown + front matter parsing

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

## Tests

```bash
pytest
```
