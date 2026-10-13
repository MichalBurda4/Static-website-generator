# Static Site Generator (SSG)

Prosty generator stron statycznych w Pythonie — projekt na Advanced Python Programming.

## Skład grupy

- Michał Burda
- Michał Broś
- Paweł Froń

## Instalacja

```bash
pip install -e ".[dev]"
```

## Struktura projektu

```
APP/
├── config.yaml          # konfiguracja strony
├── content/             # pliki Markdown ze front matter
├── templates/           # szablony Jinja2 (kolejny etap)
├── static/              # CSS, obrazy
├── output/              # wygenerowana strona (kolejny etap)
├── src/ssg/             # kod źródłowy
└── tests/               # testy
```

## Status

Zrealizowane:

1. Struktura projektu i konfiguracja
2. Parsowanie Markdown + front matter

## Przykład użycia parsera

```python
from pathlib import Path
from ssg.config import load_config
from ssg.parser import parse_markdown_file

config = load_config(Path("config.yaml"))
page = parse_markdown_file(Path("content/hello.md"))

print(page.title)
print(page.html)
```

## Testy

```bash
pytest
```
