import shutil
from datetime import date
from pathlib import Path

import yaml

from ssg.builder import SiteBuilder
from ssg.config import load_config
from ssg.parser import Page
from ssg.renderer import Renderer


def _write_project(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir()
    (tmp_path / "templates").mkdir()
    (tmp_path / "static" / "css").mkdir(parents=True)
    (tmp_path / "output").mkdir()

    (tmp_path / "config.yaml").write_text(
        yaml.dump(
            {
                "site_name": "Test Site",
                "author": "Tester",
                "description": "Demo",
                "content_dir": "content",
                "templates_dir": "templates",
                "static_dir": "static",
                "output_dir": "output",
            }
        ),
        encoding="utf-8",
    )

    (tmp_path / "content" / "hello.md").write_text(
        "---\ntitle: Hello\ndate: 2026-03-20\nslug: hello\n---\n\nHello **world**.\n",
        encoding="utf-8",
    )
    (tmp_path / "static" / "css" / "style.css").write_text(
        "body { color: black; }\n",
        encoding="utf-8",
    )

    (tmp_path / "templates" / "base.html").write_text(
        "<!DOCTYPE html><html><body>{% block content %}{% endblock %}</body></html>",
        encoding="utf-8",
    )
    (tmp_path / "templates" / "index.html").write_text(
        "{% extends 'base.html' %}{% block content %}"
        "<h1>{{ site.site_name }}</h1>"
        "{% for page in pages %}<a href='{{ page.slug }}.html'>{{ page.title }}</a>"
        "{% endfor %}{% endblock %}",
        encoding="utf-8",
    )
    (tmp_path / "templates" / "post.html").write_text(
        "{% extends 'base.html' %}{% block content %}"
        "<h1>{{ page.title }}</h1>{{ page.html | safe }}{% endblock %}",
        encoding="utf-8",
    )

    return tmp_path / "config.yaml"


def test_build_writes_index_post_and_static(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    written = SiteBuilder(config).build()

    index = tmp_path / "output" / "index.html"
    post = tmp_path / "output" / "hello.html"
    css = tmp_path / "output" / "static" / "css" / "style.css"

    assert index in written
    assert post in written
    assert index.is_file()
    assert post.is_file()
    assert css.is_file()
    assert "Test Site" in index.read_text(encoding="utf-8")
    assert "Hello" in index.read_text(encoding="utf-8")
    assert "<strong>world</strong>" in post.read_text(encoding="utf-8")


def test_renderer_uses_page_metadata(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    renderer = Renderer(config)
    page = Page(
        source_path=tmp_path / "content" / "hello.md",
        title="Hello",
        date=date(2026, 3, 20),
        html="<p>Hi</p>",
        slug="hello",
    )

    html = renderer.render_post(page)
    assert "Hello" in html
    assert "<p>Hi</p>" in html


def test_build_without_static_dir_still_writes_html(tmp_path: Path) -> None:
    config_path = _write_project(tmp_path)
    shutil.rmtree(tmp_path / "static")

    config = load_config(config_path)
    written = SiteBuilder(config).build()

    assert (tmp_path / "output" / "index.html") in written
    assert not (tmp_path / "output" / "static").exists()


def test_index_lists_posts(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    pages = [
        Page(
            source_path=tmp_path / "a.md",
            title="One",
            date=date(2026, 1, 1),
            html="<p>1</p>",
            slug="one",
            content_markdown="First line",
        )
    ]
    html = Renderer(config).render_index(pages)
    assert "One" in html
    assert "one.html" in html
