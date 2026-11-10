"""Parse Markdown files with YAML front matter."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import markdown
import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FRONT_MATTER_PATTERN = re.compile(
    r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z",
    re.DOTALL,
)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


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
        """Return a short excerpt (the first non-empty paragraph)."""
        for line in self.content_markdown.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped
        return ""


# ---------------------------------------------------------------------------
# Front matter and Markdown helpers
# ---------------------------------------------------------------------------


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Separate YAML front matter from the Markdown body.

    Returns:
        A pair ``(metadata, markdown_body)``. When there is no front matter,
        metadata is an empty dict and body is the entire text.
    """
    match = FRONT_MATTER_PATTERN.match(text)
    if not match:
        return {}, text

    metadata = _parse_front_matter_yaml(match.group(1))
    body = match.group(2)
    return metadata, body


def _parse_front_matter_yaml(raw_meta: str) -> dict[str, Any]:
    """Parse YAML front-matter text into a dictionary."""
    metadata = yaml.safe_load(raw_meta) or {}
    if not isinstance(metadata, dict):
        raise TypeError("Front matter must be a YAML key-value mapping.")
    return metadata


def markdown_to_html(text: str) -> str:
    """Convert Markdown content to HTML."""
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "nl2br"],
        output_format="html",
    )


def _normalize_date(value: Any) -> date | None:
    """Convert a front-matter date value into a ``date`` or ``None``."""
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
    """Build a URL slug from a Markdown file path."""
    return path.stem.replace("_", "-").lower()


def _title_from_metadata(metadata: dict[str, Any], path: Path) -> str:
    """Resolve the page title from metadata or the file name."""
    raw_title = metadata.get("title")
    if raw_title:
        return str(raw_title)
    return path.stem.replace("-", " ").replace("_", " ").title()


def _slug_from_metadata(metadata: dict[str, Any], path: Path) -> str:
    """Resolve the page slug from metadata or the file path."""
    raw_slug = metadata.get("slug")
    if raw_slug:
        return str(raw_slug)
    return _slug_from_path(path)


# ---------------------------------------------------------------------------
# Page loading
# ---------------------------------------------------------------------------


def parse_markdown_text(text: str, *, source_path: Path | None = None) -> Page:
    """Parse Markdown file contents (text) into a ``Page`` object."""
    path = source_path or Path("untitled.md")
    metadata, body = split_front_matter(text)
    page = Page(
        source_path=path,
        title=_title_from_metadata(metadata, path),
        date=_normalize_date(metadata.get("date")),
        metadata=metadata,
        content_markdown=body.strip("\n"),
        html=markdown_to_html(body),
        slug=_slug_from_metadata(metadata, path),
    )
    logger.debug("Parsed page %s (slug=%s)", path, page.slug)
    return page


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

    files = sorted(content_dir.rglob("*.md"))
    logger.debug("Discovered %d Markdown file(s) in %s", len(files), content_dir)
    return files


def _sort_pages(pages: list[Page]) -> list[Page]:
    """Sort pages by date (newest first), then by title."""
    return sorted(
        pages,
        key=lambda page: (page.date or date.min, page.title),
        reverse=True,
    )


def load_pages(content_dir: Path) -> list[Page]:
    """Load all pages from the ``content`` directory."""
    pages = [parse_markdown_file(path) for path in discover_markdown_files(content_dir)]
    ordered = _sort_pages(pages)
    logger.info("Loaded %d page(s) from %s", len(ordered), content_dir)
    return ordered


# ---------------------------------------------------------------------------
# Final — public API
# ---------------------------------------------------------------------------

__all__ = [
    "Page",
    "discover_markdown_files",
    "load_pages",
    "markdown_to_html",
    "parse_markdown_file",
    "parse_markdown_text",
    "split_front_matter",
]
