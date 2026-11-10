"""Load and validate generator configuration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = (
    "site_name",
    "author",
    "description",
    "content_dir",
    "templates_dir",
    "static_dir",
    "output_dir",
)


@dataclass(frozen=True)
class SiteConfig:
    """Site configuration and project paths."""

    site_name: str
    author: str
    description: str
    content_dir: Path
    templates_dir: Path
    static_dir: Path
    output_dir: Path
    root_dir: Path

    @property
    def content_path(self) -> Path:
        """Absolute path to the Markdown content directory."""
        return self.root_dir / self.content_dir

    @property
    def templates_path(self) -> Path:
        """Absolute path to the Jinja2 templates directory."""
        return self.root_dir / self.templates_dir

    @property
    def static_path(self) -> Path:
        """Absolute path to the static assets directory."""
        return self.root_dir / self.static_dir

    @property
    def output_path(self) -> Path:
        """Absolute path to the generated site directory."""
        return self.root_dir / self.output_dir


def _read_yaml_mapping(config_path: Path) -> dict[str, Any]:
    """Read a YAML file and ensure the top-level value is a mapping."""
    with config_path.open(encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    if not isinstance(raw, dict):
        raise TypeError("The configuration file must contain a key-value mapping.")
    return raw


def _missing_fields(raw: dict[str, Any]) -> list[str]:
    """Return required field names that are missing or empty."""
    return [key for key in REQUIRED_FIELDS if key not in raw or raw[key] in (None, "")]


def _build_site_config(raw: dict[str, Any], root_dir: Path) -> SiteConfig:
    """Build a ``SiteConfig`` from a validated raw mapping."""
    return SiteConfig(
        site_name=str(raw["site_name"]),
        author=str(raw["author"]),
        description=str(raw["description"]),
        content_dir=Path(str(raw["content_dir"])),
        templates_dir=Path(str(raw["templates_dir"])),
        static_dir=Path(str(raw["static_dir"])),
        output_dir=Path(str(raw["output_dir"])),
        root_dir=root_dir,
    )


def load_config(config_path: Path) -> SiteConfig:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the ``config.yaml`` file.

    Returns:
        A ``SiteConfig`` object with paths relative to the project directory.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If required fields are missing or values are invalid.
    """
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    raw = _read_yaml_mapping(config_path)
    missing = _missing_fields(raw)
    if missing:
        raise ValueError(f"Missing or empty configuration fields: {', '.join(missing)}")

    config = _build_site_config(raw, config_path.resolve().parent)
    logger.info("Loaded configuration from %s (site=%s)", config_path, config.site_name)
    return config
