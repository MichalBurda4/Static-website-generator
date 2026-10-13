from pathlib import Path

import pytest
import yaml

from ssg.config import load_config


def test_load_config_reads_expected_fields(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        yaml.dump(
            {
                "site_name": "Test Site",
                "author": "Tester",
                "description": "Opis",
                "content_dir": "content",
                "templates_dir": "templates",
                "static_dir": "static",
                "output_dir": "output",
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.site_name == "Test Site"
    assert config.author == "Tester"
    assert config.content_path == tmp_path / "content"
    assert config.output_path == tmp_path / "output"


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "brak.yaml")


def test_load_config_missing_fields_raises(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("site_name: Only Name\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Brakujące"):
        load_config(config_file)
