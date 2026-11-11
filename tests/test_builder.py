import shutil
from datetime import date
from pathlib import Path

import pytest
import yaml

from ssg.builder import SiteBuilder, _output_destination
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

    (tmp_path / "content" / "posts").mkdir()
    (tmp_path / "content" / "notes").mkdir()
    (tmp_path / "content" / "about.md").write_text(
        "---\ntitle: About\ndate: 2026-01-01\nslug: about\n---\n\nAbout page.\n",
        encoding="utf-8",
    )
    (tmp_path / "content" / "posts" / "hello.md").write_text(
        "---\ntitle: Hello\ndate: 2026-03-20\nslug: hello\n---\n\nHello **world**.\n",
        encoding="utf-8",
    )
    (tmp_path / "content" / "notes" / "extra.md").write_text(
        "---\ntitle: Extra\nslug: extra\n---\n\nExtra page.\n",
        encoding="utf-8",
    )
    (tmp_path / "static" / "css" / "style.css").write_text(
        "body { color: black; }\n",
        encoding="utf-8",
    )

    (tmp_path / "templates" / "base.html").write_text(
        "<!DOCTYPE html><html><body>"
        "<nav>{% for page in pages %}"
        "<a class='nav' href='{{ root_prefix }}{{ page.url }}'>{{ page.title }}</a>"
        "{% endfor %}</nav>"
        "<link href='{{ static_url }}css/style.css'>"
        "{% block content %}{% endblock %}</body></html>",
        encoding="utf-8",
    )
    (tmp_path / "templates" / "index.html").write_text(
        "{% extends 'base.html' %}{% block content %}"
        "<h1>{{ site.site_name }}</h1>"
        "{% for post in posts %}<a href='{{ post.url }}'>{{ post.title }}</a>"
        "{% endfor %}{% endblock %}",
        encoding="utf-8",
    )
    (tmp_path / "templates" / "post.html").write_text(
        "{% extends 'base.html' %}{% block content %}"
        "<h1>{{ page.title }}</h1>{{ page.html | safe }}"
        "<a class='home' href='{{ home_url }}'>home</a>{% endblock %}",
        encoding="utf-8",
    )

    return tmp_path / "config.yaml"


def test_build_writes_index_post_and_static(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    result = SiteBuilder(config).build()

    index = tmp_path / "output" / "index.html"
    post = tmp_path / "output" / "posts" / "hello.html"
    about = tmp_path / "output" / "about.html"
    extra = tmp_path / "output" / "notes" / "extra.html"
    css = tmp_path / "output" / "static" / "css" / "style.css"

    assert index in result.html_files
    assert post in result.html_files
    assert about in result.html_files
    assert extra in result.html_files
    assert css in result.static_files
    assert index.is_file()
    assert post.is_file()
    assert css.is_file()

    index_html = index.read_text(encoding="utf-8")
    post_html = post.read_text(encoding="utf-8")
    about_html = about.read_text(encoding="utf-8")
    assert "Test Site" in index_html
    assert "posts/hello.html" in index_html
    assert "href='about.html'>About" in index_html
    assert "extra.html" not in index_html
    assert "<strong>world</strong>" in post_html
    assert "../static/css/style.css" in post_html
    assert "href='../index.html'" in post_html
    assert "href='../about.html'" in post_html
    assert "href='static/css/style.css'" in about_html
    assert "href='index.html'" in about_html


def test_renderer_uses_page_metadata(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    renderer = Renderer(config)
    page = Page(
        source_path=tmp_path / "content" / "posts" / "hello.md",
        title="Hello",
        date=date(2026, 3, 20),
        html="<p>Hi</p>",
        slug="hello",
        url="posts/hello.html",
    )

    html = renderer.render_post(page)
    assert "Hello" in html
    assert "<p>Hi</p>" in html


def test_build_without_static_dir_still_writes_html(tmp_path: Path) -> None:
    config_path = _write_project(tmp_path)
    shutil.rmtree(tmp_path / "static")

    config = load_config(config_path)
    result = SiteBuilder(config).build()

    assert (tmp_path / "output" / "index.html") in result.html_files
    assert result.static_files == []
    assert not (tmp_path / "output" / "static").exists()


def test_copy_static_copies_css_and_images(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    images = tmp_path / "static" / "images"
    images.mkdir()
    logo = images / "logo.svg"
    logo.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")

    copied = SiteBuilder(config).copy_static()

    assert (tmp_path / "output" / "static" / "css" / "style.css") in copied
    assert (tmp_path / "output" / "static" / "images" / "logo.svg") in copied


def test_index_lists_posts(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    posts = [
        Page(
            source_path=tmp_path / "a.md",
            title="One",
            date=date(2026, 1, 1),
            html="<p>1</p>",
            slug="one",
            url="posts/one.html",
            content_markdown="First line",
        )
    ]
    html = Renderer(config).render_index(posts)
    assert "One" in html
    assert "posts/one.html" in html


def test_output_destination_rejects_absolute_url(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes the output directory"):
        _output_destination(tmp_path, "/etc/passwd.html")


def test_build_rejects_slug_that_escapes_output(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    (tmp_path / "content" / "bad.md").write_text(
        '---\ntitle: Bad\nslug: "../evil"\n---\n\nNope.\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="escapes the output directory"):
        SiteBuilder(config).build()
