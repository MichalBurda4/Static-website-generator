"""Build the static site into the output directory."""

from __future__ import annotations

import shutil
from pathlib import Path

from ssg.config import SiteConfig
from ssg.parser import Page, load_pages
from ssg.renderer import Renderer


class SiteBuilder:
    """Orchestrate: content → templates → files in ``output/``."""

    def __init__(self, config: SiteConfig) -> None:
        self._config = config
        self._renderer = Renderer(config)

    def build(self) -> list[Path]:
        """Generate the homepage, post pages, and copy static assets.

        Returns:
            Paths of HTML files written to the output directory.
        """
        output = self._config.output_path
        output.mkdir(parents=True, exist_ok=True)

        pages = load_pages(self._config.content_path)
        written: list[Path] = []

        index_path = output / "index.html"
        index_path.write_text(self._renderer.render_index(pages), encoding="utf-8")
        written.append(index_path)

        for page in pages:
            path = self._write_post(output, page)
            written.append(path)

        self._copy_static(output)
        return written

    def _write_post(self, output: Path, page: Page) -> Path:
        path = output / f"{page.slug}.html"
        path.write_text(self._renderer.render_post(page), encoding="utf-8")
        return path

    def _copy_static(self, output: Path) -> None:
        """Copy ``static/`` into ``output/static/`` so CSS works in the built site.

        Uses ``dirs_exist_ok`` instead of deleting the target first — OneDrive on
        Windows often locks ``output/`` and makes ``rmtree`` fail with Access Denied.
        """
        source = self._config.static_path
        target = output / "static"
        if not source.is_dir():
            return
        shutil.copytree(source, target, dirs_exist_ok=True)
