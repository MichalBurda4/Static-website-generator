# Static Site Generator (SSG)

A simple static site generator written in Python — project for *Advanced Python Programming* (AGH).

## Team

- Michał Burda
- Michał Broś
- Paweł Froń

## Requirements

- Python ≥ 3.14
- [`uv`](https://docs.astral.sh/uv/)

## Quick start

```powershell
uv sync
uv run ssg build
uv run python -m http.server -d output -b localhost 8000
```

Then open [http://localhost:8000](http://localhost:8000).

If you have `make`:

```bash
make setup
make build
make view-output
```

## CLI commands

| Command | Description |
|---------|-------------|
| `uv run ssg build` | Generate HTML into `output/` and copy `static/` |
| `uv run ssg parse` | Print parsed Markdown pages (no write) |
| `uv run ssg --version` | Show version |
| `uv run ssg build --config path.yaml` | Build with a custom config file |

Equivalent: `uv run python -m ssg build`.

Generated files land in `output/` (`index.html`, root pages beside it, and nested pages mirroring folders under `content/`).
Static assets from `static/` are copied to `output/static/`.

## Configuration (`config.yaml`)

```yaml
site_name: "Mój Blog"
author: "..."
description: "..."
theme: light          # light | dark
content_dir: "content"
templates_dir: "templates"
static_dir: "static"
output_dir: "output"
```

| Theme | Stylesheet |
|-------|------------|
| `light` (default) | `static/css/light.css` |
| `dark` | `static/css/dark.css` |

Rebuild after changing `theme` (`uv run ssg build`).

## Project structure

```
APP/
├── config.yaml       # site configuration
├── content/          # Markdown + YAML front matter
├── templates/        # Jinja2 templates
├── static/           # CSS, images
├── output/           # build output
├── src/ssg/          # generator source
├── tests/            # unit tests
└── docs/             # documentation
```

Modules in `src/ssg/`:

| Module | Role |
|--------|------|
| `config.py` | load and validate YAML |
| `parser.py` | front matter + Markdown → HTML |
| `renderer.py` | Jinja2 templates |
| `builder.py` | write pages + copy static assets |
| `cli.py` | command-line interface |

## Writing content

Put `.md` files in `content/` (subfolders allowed; folder layout is mirrored in `output/`). Each directory directly inside `content/` is passed to templates under that directory's name, so `content/posts/` is the `posts` list on the homepage. Front matter:

```markdown
---
title: Post title
date: 2026-11-09
slug: my-post
template: post
---

Body in **Markdown**.
```

`template` is required and selects the Jinja file (`post` loads `templates/post.html`). Header links are written in `templates/base.html`.

Details: [docs/writing-content.md](docs/writing-content.md).

## Tests

```powershell
uv run pytest
uv run pytest --cov=ssg --cov-report=term-missing
```

With Make: `make test` (setup + HTML coverage under `.artifacts/coverage/html/`).

## Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python ≥ 3.14 |
| Dependencies | uv / pyproject.toml |
| Configuration | PyYAML |
| Content | markdown + YAML front matter |
| Templates | Jinja2 |
| Tests / quality | pytest, pytest-cov, ruff, pyright, pre-commit |

## Documentation

Technical documentation (PDF): [`docs/Technical-Documentation.pdf`](docs/Technical-Documentation.pdf).
