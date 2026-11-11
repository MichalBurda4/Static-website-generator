"""Build the static site into the output directory."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from ssg.config import SiteConfig
from ssg.parser import Page, load_pages
from ssg.renderer import Renderer

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BuildResult:
    """Paths produced by a site build.

    Attributes:
        html_files: Generated HTML files, homepage first, then posts.
        static_files: Files copied into ``output/static``. Empty when the
            static directory is missing.
    """

    html_files: list[Path]
    static_files: list[Path]


class SiteBuilder:
    """Orchestrate: content → templates → files in ``output/``."""

    def __init__(self, config: SiteConfig) -> None:
        """Create a builder bound to the given site configuration.

        Args:
            config: Loaded site configuration and project paths.
        """
        self._config = config
        self._renderer = Renderer(config)

    def build(self) -> BuildResult:
        """Generate the homepage, post pages, and copy static assets.

        Returns:
            Paths of the written HTML files and copied static files.

        Raises:
            FileNotFoundError: If the content directory does not exist.
            jinja2.TemplateNotFound: If a required template is missing.
            TypeError: If a page's front matter is not a YAML mapping.
            ValueError: If a page's date is not a supported format.
            yaml.YAMLError: If a page's front matter is not valid YAML.
        """
        output = self._prepare_output()
        pages = load_pages(self._config.content_path)

        html_files = [self._write_index(output, pages)]
        html_files.extend(self._write_posts(output, pages))
        static_files = self.copy_static(output)

        logger.info(
            "Build finished: %d HTML file(s), %d static file(s)",
            len(html_files),
            len(static_files),
        )
        return BuildResult(html_files=html_files, static_files=static_files)

    def _prepare_output(self) -> Path:
        """Ensure the output directory exists and return its path.

        Returns:
            The output directory, created when it was missing.
        """
        output = self._config.output_path
        output.mkdir(parents=True, exist_ok=True)
        logger.debug("Output directory ready: %s", output)
        return output

    def _write_index(self, output: Path, pages: list[Page]) -> Path:
        """Render and write the homepage.

        Args:
            output: Directory that receives ``index.html``.
            pages: Pages listed on the homepage.

        Returns:
            Path of the written ``index.html``.

        Raises:
            jinja2.TemplateNotFound: If ``index.html`` is not in the
                templates directory.
        """
        index_path = output / "index.html"
        index_path.write_text(self._renderer.render_index(pages), encoding="utf-8")
        logger.info("Wrote homepage: %s", index_path)
        return index_path

    def _write_posts(self, output: Path, pages: list[Page]) -> list[Path]:
        """Render and write one HTML file per page.

        Args:
            output: Directory that receives the post files.
            pages: Pages to render.

        Returns:
            Paths of the written post files, in ``pages`` order.

        Raises:
            jinja2.TemplateNotFound: If ``post.html`` is not in the
                templates directory.
        """
        return [self._write_post(output, page) for page in pages]

    def _write_post(self, output: Path, page: Page) -> Path:
        """Render and write a single post page.

        Args:
            output: Directory that receives the file.
            page: Page to render. The file name is ``{page.slug}.html``.

        Returns:
            Path of the written HTML file.

        Raises:
            jinja2.TemplateNotFound: If ``post.html`` is not in the
                templates directory.
        """
        path = output / f"{page.slug}.html"
        path.write_text(self._renderer.render_post(page), encoding="utf-8")
        logger.info("Wrote post: %s", path)
        return path

    def copy_static(self, output: Path | None = None) -> list[Path]:
        """Copy ``static/`` into ``output/static/`` and return copied file paths.

        Uses ``dirs_exist_ok`` instead of deleting the target first — OneDrive on
        Windows often locks ``output/`` and makes ``rmtree`` fail with Access Denied.

        Args:
            output: Destination site directory. Defaults to the configured
                output path.

        Returns:
            Paths of files under ``output/static``, sorted. Empty when the
            source static directory does not exist.
        """
        source = self._config.static_path
        target = (output or self._config.output_path) / "static"

        if not source.is_dir():
            logger.warning("Static directory missing, skipping copy: %s", source)
            return []

        shutil.copytree(source, target, dirs_exist_ok=True)
        copied = sorted(path for path in target.rglob("*") if path.is_file())
        logger.info(
            "Copied %d static file(s) from %s to %s",
            len(copied),
            source,
            target,
        )
        return copied
