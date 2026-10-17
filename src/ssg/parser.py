"""Parse Markdown files with YAML front matter."""

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
    """A single page loaded from a Markdown file."""

    source_path: Path
    title: str
    date: date | None
    metadata: dict[str, Any] = field(default_factory=dict)
    content_markdown: str = ""
    html: str = ""
    slug: str = ""

    @property
    def excerpt(self) -> str:
        """A short excerpt (the first non-empty paragraph)."""
        for line in self.content_markdown.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped
        return ""


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Separate YAML front matter from the Markdown body.

    Returns:
        A pair ``(metadata, markdown_body)``. When there is no front matter,
        metadata is an empty dict and body is the entire text.
    """
    match = FRONT_MATTER_PATTERN.match(text)
    if not match:
        return {}, text

    raw_meta = match.group(1)
    body = match.group(2)

    metadata = yaml.safe_load(raw_meta) or {}
    if not isinstance(metadata, dict):
        raise TypeError("Front matter must be a YAML key-value mapping.")

    return metadata, body


def markdown_to_html(text: str) -> str:
    """Convert Markdown content to HTML."""
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
    raise ValueError(f"Unsupported date format: {value!r}")


def _slug_from_path(path: Path) -> str:
    return path.stem.replace("_", "-").lower()


def parse_markdown_text(text: str, *, source_path: Path | None = None) -> Page:
    """Parse Markdown file contents (text) into a ``Page`` object."""
    path = source_path or Path("untitled.md")
    metadata, body = split_front_matter(text)

    title = str(
        metadata.get("title") or path.stem.replace("-", " ").replace("_", " ").title()
    )
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
    """Load and parse a ``.md`` file."""
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    text = path.read_text(encoding="utf-8")
    return parse_markdown_text(text, source_path=path)


def discover_markdown_files(content_dir: Path) -> list[Path]:
    """Find all Markdown files in the content directory (recursively)."""
    if not content_dir.is_dir():
        raise FileNotFoundError(f"Content directory not found: {content_dir}")

    return sorted(content_dir.rglob("*.md"))


def load_pages(content_dir: Path) -> list[Page]:
    """Load all pages from the ``content`` directory."""
    pages = [parse_markdown_file(path) for path in discover_markdown_files(content_dir)]
    return sorted(
        pages,
        key=lambda page: (page.date or date.min, page.title),
        reverse=True,
    )
