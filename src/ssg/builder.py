"""Build the static site into the output directory."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

from ssg.config import SiteConfig
from ssg.parser import Page, load_pages
from ssg.renderer import Renderer

logger = logging.getLogger(__name__)

_RESERVED_TEMPLATE_VARIABLES: Final[frozenset[str]] = frozenset(
    {"site", "page", "home_url", "static_url", "root_prefix"}
)


@dataclass(frozen=True, slots=True)
class BuildResult:
    """Paths produced by a site build.

    Attributes:
        html_files: Generated HTML files, homepage first, then content pages.
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
        """Generate the homepage, content pages, and copy static assets.

        Returns:
            Paths of the written HTML files and copied static files.

        Raises:
            FileNotFoundError: If the content directory does not exist.
            jinja2.TemplateNotFound: If a required template is missing.
            TypeError: If a page's front matter is not a YAML mapping.
            ValueError: If a page's date or template name is invalid, a
                content directory name cannot be a template variable, or a
                page URL escapes the output directory.
            yaml.YAMLError: If a page's front matter is not valid YAML.
        """
        output = self._prepare_output()
        content_dir = self._config.content_path
        documents = load_pages(content_dir)
        collections = _content_collections(documents, content_dir)

        html_files = [self._write_index(output, collections)]
        html_files.extend(self._write_documents(output, documents, collections))
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

    def _write_index(self, output: Path, collections: dict[str, list[Page]]) -> Path:
        """Render and write the homepage.

        Args:
            output: Directory that receives ``index.html``.
            collections: Pages grouped by their top-level content directory.

        Returns:
            Path of the written ``index.html``.

        Raises:
            jinja2.TemplateNotFound: If ``index.html`` is not in the
                templates directory.
        """
        index_path = output / "index.html"
        index_path.write_text(
            self._renderer.render_index(collections),
            encoding="utf-8",
        )
        logger.info("Wrote homepage: %s", index_path)
        return index_path

    def _write_documents(
        self,
        output: Path,
        documents: list[Page],
        collections: dict[str, list[Page]],
    ) -> list[Path]:
        """Render and write one HTML file per content document.

        Args:
            output: Directory that receives the HTML files.
            documents: Documents to render. Folders under ``content/`` are kept.
            collections: Pages grouped by their top-level content directory.

        Returns:
            Paths of the written HTML files, in ``documents`` order.

        Raises:
            jinja2.TemplateNotFound: If a page's template is not in the
                templates directory.
            ValueError: If a document URL escapes the output directory.
        """
        return [
            self._write_document(output, document, collections)
            for document in documents
        ]

    def _write_document(
        self,
        output: Path,
        page: Page,
        collections: dict[str, list[Page]],
    ) -> Path:
        """Render and write a single content page.

        Args:
            output: Directory that receives the file.
            page: Page to render. The path is ``page.url`` under ``output``.
            collections: Pages grouped by their top-level content directory.

        Returns:
            Path of the written HTML file.

        Raises:
            jinja2.TemplateNotFound: If ``page.template`` is not in the
                templates directory.
            ValueError: If ``page.url`` escapes the output directory.
        """
        path = _output_destination(output, page.url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self._renderer.render_page(page, collections),
            encoding="utf-8",
        )
        logger.info("Wrote page: %s", path)
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


def _relative_to_content(page: Page, content_dir: Path) -> Path:
    """Return a page's source path relative to the content directory.

    Args:
        page: Page whose ``source_path`` lives inside ``content_dir``.
        content_dir: Root directory of Markdown sources.

    Returns:
        The source path relative to ``content_dir``.
    """
    return page.source_path.resolve().relative_to(content_dir.resolve())


def _content_collections(
    documents: list[Page],
    content_dir: Path,
) -> dict[str, list[Page]]:
    """Group pages by their top-level directory under ``content_dir``.

    Args:
        documents: Pages to group. Order inside each group is preserved.
        content_dir: Root directory of Markdown sources.

    Returns:
        A mapping from directory name to the pages inside it. Files placed
        directly in ``content_dir`` are omitted. Nested files stay in the
        top-level directory's list.

    Raises:
        ValueError: If a directory name is not an identifier, or would
            overwrite a reserved template variable.
    """
    collections: dict[str, list[Page]] = {}
    for page in documents:
        relative = _relative_to_content(page, content_dir)
        if len(relative.parts) == 1:
            continue
        name = relative.parts[0]
        if not name.isidentifier() or name in _RESERVED_TEMPLATE_VARIABLES:
            raise ValueError(
                f"{page.source_path}: content directory name cannot be a "
                f"template variable: {name}"
            )
        collections.setdefault(name, []).append(page)
    return collections


def _output_destination(output: Path, url: str) -> Path:
    """Resolve a site-relative URL to a file inside ``output``.

    Args:
        output: Generated site directory.
        url: Site-relative HTML path, such as ``posts/drugi-wpis.html``.

    Returns:
        The absolute destination path.

    Raises:
        ValueError: If ``url`` is absolute or contains ``..``.
    """
    relative = PurePosixPath(url)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Page URL escapes the output directory: {url}")
    return output.joinpath(*relative.parts)
