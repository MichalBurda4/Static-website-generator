from datetime import date
from pathlib import Path

import pytest

from ssg.parser import (
    load_pages,
    parse_markdown_file,
    parse_markdown_text,
    split_front_matter,
)


SAMPLE = """---
title: Przykład
date: 2026-03-20
tags:
  - python
  - ssg
---

# Nagłówek

Treść z **Markdown**.
"""


def test_split_front_matter_extracts_metadata_and_body() -> None:
    metadata, body = split_front_matter(SAMPLE)

    assert metadata["title"] == "Przykład"
    assert metadata["date"] == date(2026, 3, 20)
    assert metadata["tags"] == ["python", "ssg"]
    assert body.strip().startswith("# Nagłówek")


def test_split_front_matter_without_header_returns_empty_meta() -> None:
    metadata, body = split_front_matter("# Sam Markdown\n")

    assert metadata == {}
    assert body == "# Sam Markdown\n"


def test_parse_markdown_text_builds_page() -> None:
    page = parse_markdown_text(SAMPLE, source_path=Path("przyklad.md"))

    assert page.title == "Przykład"
    assert page.date == date(2026, 3, 20)
    assert page.slug == "przyklad"
    assert "<strong>Markdown</strong>" in page.html
    assert page.excerpt.startswith("Treść")


def test_parse_markdown_file_and_load_pages(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    posts_dir = content_dir / "posts"
    posts_dir.mkdir(parents=True)

    (content_dir / "a.md").write_text(
        "---\ntitle: Starszy\ndate: 2026-01-01\n---\n\nA\n",
        encoding="utf-8",
    )
    (posts_dir / "b.md").write_text(
        "---\ntitle: Nowszy\ndate: 2026-02-01\n---\n\nB\n",
        encoding="utf-8",
    )

    page = parse_markdown_file(content_dir / "a.md")
    assert page.title == "Starszy"

    pages = load_pages(content_dir)
    assert [p.title for p in pages] == ["Nowszy", "Starszy"]


def test_parse_markdown_file_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_markdown_file(tmp_path / "brak.md")
