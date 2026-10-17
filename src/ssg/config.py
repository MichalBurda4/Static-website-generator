"""Load and validate generator configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


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
        return self.root_dir / self.content_dir

    @property
    def templates_path(self) -> Path:
        return self.root_dir / self.templates_dir

    @property
    def static_path(self) -> Path:
        return self.root_dir / self.static_dir

    @property
    def output_path(self) -> Path:
        return self.root_dir / self.output_dir


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

    with config_path.open(encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    if not isinstance(raw, dict):
        raise TypeError("The configuration file must contain a key-value mapping.")

    required = (
        "site_name",
        "author",
        "description",
        "content_dir",
        "templates_dir",
        "static_dir",
        "output_dir",
    )
    missing = [key for key in required if key not in raw or raw[key] in (None, "")]
    if missing:
        raise ValueError(f"Missing or empty configuration fields: {', '.join(missing)}")

    root_dir = config_path.resolve().parent

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
