from pathlib import Path

import yaml

from ssg.cli import main


def _mini_project(tmp_path: Path) -> Path:
    (tmp_path / "content").mkdir()
    (tmp_path / "templates").mkdir()
    (tmp_path / "static" / "css").mkdir(parents=True)
    (tmp_path / "output").mkdir()

    config = tmp_path / "config.yaml"
    config.write_text(
        yaml.dump(
            {
                "site_name": "CLI Site",
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
    (tmp_path / "content" / "post.md").write_text(
        "---\ntitle: Post\ndate: 2026-03-20\nslug: post\n---\n\nBody\n",
        encoding="utf-8",
    )
    (tmp_path / "static" / "css" / "style.css").write_text("body{}", encoding="utf-8")
    (tmp_path / "templates" / "base.html").write_text(
        "<html>{% block content %}{% endblock %}</html>",
        encoding="utf-8",
    )
    (tmp_path / "templates" / "index.html").write_text(
        "{% extends 'base.html' %}{% block content %}index{% endblock %}",
        encoding="utf-8",
    )
    (tmp_path / "templates" / "post.html").write_text(
        "{% extends 'base.html' %}{% block content %}{{ page.title }}{% endblock %}",
        encoding="utf-8",
    )
    return config


def test_cli_parse_prints_pages(tmp_path: Path, capsys, monkeypatch) -> None:
    config = _mini_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["parse", "--config", str(config)])

    out = capsys.readouterr().out
    assert "CLI Site" in out
    assert "Post" in out


def test_cli_parse_empty_content(tmp_path: Path, capsys, monkeypatch) -> None:
    config = _mini_project(tmp_path)
    for path in (tmp_path / "content").glob("**/*.md"):
        path.unlink()
    monkeypatch.chdir(tmp_path)

    main(["parse", "--config", str(config)])

    assert "No Markdown files" in capsys.readouterr().out


def test_cli_build_writes_output(tmp_path: Path, capsys, monkeypatch) -> None:
    config = _mini_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["build", "--config", str(config)])

    out = capsys.readouterr().out
    assert "Built" in out
    assert (tmp_path / "output" / "index.html").is_file()
    assert (tmp_path / "output" / "post.html").is_file()


def test_cli_without_command_prints_help(capsys) -> None:
    main([])
    assert "static site generator" in capsys.readouterr().out.lower()
