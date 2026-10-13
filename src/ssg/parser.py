"""Parsowanie plików Markdown z front matter YAML."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import markdown
import yaml

FRONT_MATTER_PATTERN = re.compile(
    r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z",
    re.DOTALL,
)


@dataclass(frozen=True)
class Page:
    """Pojedyncza strona wczytana z pliku Markdown."""

    source_path: Path
    title: str
    date: date | None
    metadata: dict[str, Any] = field(default_factory=dict)
    content_markdown: str = ""
    html: str = ""
    slug: str = ""

    @property
    def excerpt(self) -> str:
        """Krótki fragment treści (pierwszy niepusty akapit)."""
        for line in self.content_markdown.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped
        return ""


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Oddziel front matter YAML od treści Markdown.

    Returns:
        Para ``(metadata, markdown_body)``. Gdy brak front matter,
        metadata jest pustym słownikiem, a body to cały tekst.
    """
    match = FRONT_MATTER_PATTERN.match(text)
    if not match:
        return {}, text

    raw_meta = match.group(1)
    body = match.group(2)

    metadata = yaml.safe_load(raw_meta) or {}
    if not isinstance(metadata, dict):
        raise ValueError("Front matter musi być mapowaniem klucz-wartość YAML.")

    return metadata, body


def markdown_to_html(text: str) -> str:
    """Konwertuj treść Markdown na HTML."""
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "nl2br"],
        output_format="html",
    )


def _normalize_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError(f"Nieobsługiwany format daty: {value!r}")


def _slug_from_path(path: Path) -> str:
    return path.stem.replace("_", "-").lower()


def parse_markdown_text(text: str, *, source_path: Path | None = None) -> Page:
    """Sparsuj treść pliku Markdown (tekst) do obiektu ``Page``."""
    path = source_path or Path("untitled.md")
    metadata, body = split_front_matter(text)

    title = str(metadata.get("title") or path.stem.replace("-", " ").replace("_", " ").title())
    page_date = _normalize_date(metadata.get("date"))
    slug = str(metadata.get("slug") or _slug_from_path(path))

    return Page(
        source_path=path,
        title=title,
        date=page_date,
        metadata=metadata,
        content_markdown=body.strip("\n"),
        html=markdown_to_html(body),
        slug=slug,
    )


def parse_markdown_file(path: Path) -> Page:
    """Wczytaj i sparsuj plik ``.md``."""
    if not path.is_file():
        raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

    text = path.read_text(encoding="utf-8")
    return parse_markdown_text(text, source_path=path)


def discover_markdown_files(content_dir: Path) -> list[Path]:
    """Znajdź wszystkie pliki Markdown w katalogu treści (rekurencyjnie)."""
    if not content_dir.is_dir():
        raise FileNotFoundError(f"Nie znaleziono katalogu treści: {content_dir}")

    return sorted(content_dir.rglob("*.md"))


def load_pages(content_dir: Path) -> list[Page]:
    """Wczytaj wszystkie strony z katalogu ``content``."""
    pages = [parse_markdown_file(path) for path in discover_markdown_files(content_dir)]
    return sorted(
        pages,
        key=lambda page: (page.date or date.min, page.title),
        reverse=True,
    )
