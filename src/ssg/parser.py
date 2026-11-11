"""Parse Markdown files with YAML front matter."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Final

import markdown
import yaml

logger = logging.getLogger(__name__)

FRONT_MATTER_PATTERN: Final[re.Pattern] = re.compile(
    r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z",
    re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class Page:
    """A single page loaded from a Markdown file.

    Attributes:
        source_path: Filesystem path of the source Markdown file.
        title: Page title from front matter, or derived from the file name.
        date: Publication date from front matter, or ``None`` when absent.
        metadata: Raw front-matter mapping. Empty when the file has none.
        content_markdown: Markdown body with the front matter removed.
        html: Body converted to HTML.
        slug: URL slug used as the output file name.
    """

    source_path: Path
    title: str
    date: date | None
    metadata: dict[str, Any] = field(default_factory=dict)
    content_markdown: str = ""
    html: str = ""
    slug: str = ""

    @property
    def excerpt(self) -> str:
        """Return a short excerpt (the first non-empty paragraph).

        Returns:
            The first non-empty, non-heading line of the Markdown body,
            or an empty string when the body has none.
        """
        for line in self.content_markdown.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped
        return ""


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Separate YAML front matter from the Markdown body.

    Args:
        text: Full Markdown file contents, optionally starting with front matter.

    Returns:
        A pair ``(metadata, markdown_body)``. When there is no front matter,
        metadata is an empty dict and body is the entire text.

    Raises:
        TypeError: If the front matter is not a YAML mapping.
        yaml.YAMLError: If the front matter is not valid YAML.
    """
    match = FRONT_MATTER_PATTERN.match(text)
    if not match:
        return {}, text

    metadata = _parse_front_matter_yaml(match.group(1))
    body = match.group(2)
    return metadata, body


def _parse_front_matter_yaml(raw_meta: str) -> dict[str, Any]:
    """Parse YAML front-matter text into a dictionary.

    Args:
        raw_meta: YAML text between the front-matter delimiters.

    Returns:
        The parsed mapping. An empty document becomes an empty dict.

    Raises:
        TypeError: If the parsed value is not a mapping.
        yaml.YAMLError: If ``raw_meta`` is not valid YAML.
    """
    metadata = yaml.safe_load(raw_meta) or {}
    if not isinstance(metadata, dict):
        raise TypeError("Front matter must be a YAML key-value mapping.")
    return metadata


def markdown_to_html(text: str) -> str:
    """Convert Markdown content to HTML.

    Args:
        text: Markdown source to convert.

    Returns:
        HTML produced with the fenced-code, tables, and nl2br extensions.
    """
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "nl2br"],
        output_format="html",
    )


def _normalize_date(value: Any) -> date | None:
    """Convert a front-matter date value into a ``date`` or ``None``.

    Args:
        value: Date from front matter. ``None`` and ``""`` mean no date.
            ``datetime`` values are reduced to a calendar date. Strings must
            be ISO-8601 dates (``YYYY-MM-DD``).

    Returns:
        The corresponding ``date``, or ``None`` when ``value`` is missing.

    Raises:
        ValueError: If ``value`` is not a supported date format.
    """
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
    """Build a URL slug from a Markdown file path.

    Args:
        path: Source Markdown path. Only the file stem is used.

    Returns:
        The stem in lowercase, with underscores replaced by hyphens.
    """
    return path.stem.replace("_", "-").lower()


def _title_from_metadata(metadata: dict[str, Any], path: Path) -> str:
    """Resolve the page title from metadata or the file name.

    Args:
        metadata: Parsed front-matter mapping.
        path: Source Markdown path, used when ``title`` is missing.

    Returns:
        The front-matter title, or a title derived from the file stem.
    """
    raw_title = metadata.get("title")
    if raw_title:
        return str(raw_title)
    return path.stem.replace("-", " ").replace("_", " ").title()


def _slug_from_metadata(metadata: dict[str, Any], path: Path) -> str:
    """Resolve the page slug from metadata or the file path.

    Args:
        metadata: Parsed front-matter mapping.
        path: Source Markdown path, used when ``slug`` is missing.

    Returns:
        The front-matter slug, or a slug derived from ``path``.
    """
    raw_slug = metadata.get("slug")
    if raw_slug:
        return str(raw_slug)
    return _slug_from_path(path)


def parse_markdown_text(text: str, *, source_path: Path | None = None) -> Page:
    """Parse Markdown file contents (text) into a ``Page`` object.

    Args:
        text: Full Markdown file contents, with optional YAML front matter.
        source_path: Path recorded on the page. Defaults to ``untitled.md``.

    Returns:
        A ``Page`` with title, date, slug, Markdown body, and HTML.

    Raises:
        TypeError: If the front matter is not a YAML mapping.
        ValueError: If the front-matter date is not a supported format.
        yaml.YAMLError: If the front matter is not valid YAML.
    """
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
    """Load and parse a ``.md`` file.

    Args:
        path: Path to a UTF-8 Markdown file.

    Returns:
        The parsed page.

    Raises:
        FileNotFoundError: If ``path`` is not a file.
        TypeError: If the front matter is not a YAML mapping.
        ValueError: If the front-matter date is not a supported format.
        yaml.YAMLError: If the front matter is not valid YAML.
    """
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    text = path.read_text(encoding="utf-8")
    return parse_markdown_text(text, source_path=path)


def discover_markdown_files(content_dir: Path) -> list[Path]:
    """Find all Markdown files in the content directory (recursively).

    Args:
        content_dir: Directory to search for ``*.md`` files.

    Returns:
        Matching paths, sorted by path.

    Raises:
        FileNotFoundError: If ``content_dir`` is not a directory.
    """
    if not content_dir.is_dir():
        raise FileNotFoundError(f"Content directory not found: {content_dir}")

    files = sorted(content_dir.rglob("*.md"))
    logger.debug("Discovered %d Markdown file(s) in %s", len(files), content_dir)
    return files


def _sort_pages(pages: list[Page]) -> list[Page]:
    """Sort pages by date (newest first), then by title.

    Args:
        pages: Pages to order. The input list is not modified.

    Returns:
        A new list ordered by date descending, then by title descending.
        Pages without a date are treated as the oldest.
    """
    return sorted(
        pages,
        key=lambda page: (page.date or date.min, page.title),
        reverse=True,
    )


def load_pages(content_dir: Path) -> list[Page]:
    """Load all pages from the ``content`` directory.

    Args:
        content_dir: Directory of Markdown source files.

    Returns:
        Parsed pages sorted by date (newest first), then by title.

    Raises:
        FileNotFoundError: If ``content_dir`` does not exist.
        TypeError: If a page's front matter is not a YAML mapping.
        ValueError: If a page's date is not a supported format.
        yaml.YAMLError: If a page's front matter is not valid YAML.
    """
    pages = [parse_markdown_file(path) for path in discover_markdown_files(content_dir)]
    ordered = _sort_pages(pages)
    logger.info("Loaded %d page(s) from %s", len(ordered), content_dir)
    return ordered
