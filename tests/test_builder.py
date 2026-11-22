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
        "---\ntitle: About\ndate: 2026-01-01\nslug: about\ntemplate: post\n---\n\nAbout page.\n",
        encoding="utf-8",
    )
    (tmp_path / "content" / "posts" / "hello.md").write_text(
        "---\ntitle: Hello\ndate: 2026-03-20\nslug: hello\ntemplate: post\n---\n\nHello **world**.\n",
        encoding="utf-8",
    )
    (tmp_path / "content" / "notes" / "extra.md").write_text(
        "---\ntitle: Extra\nslug: extra\ntemplate: post\n---\n\nExtra page.\n",
        encoding="utf-8",
    )
    (tmp_path / "static" / "css" / "light.css").write_text(
        "body { color: black; }\n",
        encoding="utf-8",
    )
    (tmp_path / "static" / "css" / "dark.css").write_text(
        "body { color: white; }\n",
        encoding="utf-8",
    )

    (tmp_path / "templates" / "base.html").write_text(
        "<!DOCTYPE html><html><body>"
        "<nav><a class='nav' href='{{ root_prefix }}about.html'>About</a></nav>"
        "<link href='{{ static_url }}{{ site.stylesheet }}'>"
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
    css = tmp_path / "output" / "static" / "css" / "light.css"

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
    assert "../static/css/light.css" in post_html
    assert "href='../index.html'" in post_html
    assert "href='../about.html'" in post_html
    assert "href='static/css/light.css'" in about_html
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
        template="post.html",
        url="posts/hello.html",
    )

    html = renderer.render_page(page)
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

    assert (tmp_path / "output" / "static" / "css" / "light.css") in copied
    assert (tmp_path / "output" / "static" / "images" / "logo.svg") in copied


def test_build_links_selected_theme_stylesheet(tmp_path: Path) -> None:
    config_path = _write_project(tmp_path)
    (tmp_path / "templates" / "base.html").write_text(
        '<link rel="stylesheet" href="{{ static_url }}{{ site.stylesheet }}">'
        "{% block content %}{% endblock %}",
        encoding="utf-8",
    )
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raw["theme"] = "dark"
    config_path.write_text(yaml.dump(raw), encoding="utf-8")

    config = load_config(config_path)
    SiteBuilder(config).build()

    index_html = (tmp_path / "output" / "index.html").read_text(encoding="utf-8")
    assert "static/css/dark.css" in index_html


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
    html = Renderer(config).render_index({"posts": posts})
    assert "One" in html
    assert "posts/one.html" in html


def test_build_renders_page_with_declared_template(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    (tmp_path / "templates" / "card.html").write_text(
        "{% extends 'base.html' %}{% block content %}CARD {{ page.title }}{% endblock %}",
        encoding="utf-8",
    )
    (tmp_path / "content" / "about.md").write_text(
        "---\ntitle: About\ntemplate: card\nslug: about\n---\n\nAbout page.\n",
        encoding="utf-8",
    )

    SiteBuilder(config).build()

    about_html = (tmp_path / "output" / "about.html").read_text(encoding="utf-8")
    assert "CARD About" in about_html


def test_index_receives_each_content_directory(tmp_path: Path) -> None:
    config_path = _write_project(tmp_path)
    (tmp_path / "templates" / "index.html").write_text(
        "{% extends 'base.html' %}{% block content %}"
        "{% for note in notes %}<a href='{{ note.url }}'>{{ note.title }}</a>"
        "{% endfor %}{% endblock %}",
        encoding="utf-8",
    )

    SiteBuilder(load_config(config_path)).build()

    index_html = (tmp_path / "output" / "index.html").read_text(encoding="utf-8")
    assert "notes/extra.html" in index_html
    assert "posts/hello.html" not in index_html


def test_nested_directory_stays_in_top_level_collection(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    nested = tmp_path / "content" / "posts" / "2026"
    nested.mkdir()
    (nested / "older.md").write_text(
        "---\ntitle: Older\ndate: 2020-01-01\ntemplate: post\nslug: older\n---\n\nOld.\n",
        encoding="utf-8",
    )

    SiteBuilder(config).build()

    index_html = (tmp_path / "output" / "index.html").read_text(encoding="utf-8")
    assert "posts/2026/older.html" in index_html
    assert (tmp_path / "output" / "posts" / "2026" / "older.html").is_file()


@pytest.mark.parametrize("dirname", ["page", "my-notes"])
def test_build_rejects_unusable_collection_name(tmp_path: Path, dirname: str) -> None:
    config = load_config(_write_project(tmp_path))
    folder = tmp_path / "content" / dirname
    folder.mkdir()
    (folder / "x.md").write_text(
        "---\ntitle: X\ntemplate: post\n---\n\nX\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="template variable"):
        SiteBuilder(config).build()


def test_build_rejects_missing_template(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    (tmp_path / "content" / "bare.md").write_text(
        "# No front matter\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="template"):
        SiteBuilder(config).build()


def test_output_destination_rejects_absolute_url(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes the output directory"):
        _output_destination(tmp_path, "/etc/passwd.html")


def test_build_rejects_slug_that_escapes_output(tmp_path: Path) -> None:
    config = load_config(_write_project(tmp_path))
    (tmp_path / "content" / "bad.md").write_text(
        '---\ntitle: Bad\nslug: "../evil"\ntemplate: post\n---\n\nNope.\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="escapes the output directory"):
        SiteBuilder(config).build()
