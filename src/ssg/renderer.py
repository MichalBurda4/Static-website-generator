"""Render HTML pages with Jinja2 templates."""

from __future__ import annotations

import logging
from pathlib import PurePosixPath

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ssg.config import SiteConfig
from ssg.parser import Page

logger = logging.getLogger(__name__)


class Renderer:
    """Load templates from disk and render pages / the homepage."""

    def __init__(self, config: SiteConfig) -> None:
        """Create a renderer that loads templates from the configured directory.

        Args:
            config: Site configuration. Templates are loaded from
                ``config.templates_path``.
        """
        self._config = config
        self._env = Environment(
            loader=FileSystemLoader(str(config.templates_path)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        logger.debug("Renderer ready (templates=%s)", config.templates_path)

    def render_index(self, collections: dict[str, list[Page]] | None = None) -> str:
        """Render the homepage.

        Args:
            collections: Pages grouped by the top-level content directory
                that contains them. Each directory name is a template
                variable. Defaults to an empty mapping.

        Returns:
            Rendered homepage HTML.

        Raises:
            jinja2.TemplateNotFound: If ``index.html`` is missing.
        """
        groups = {} if collections is None else collections
        template = self._env.get_template("index.html")
        html = template.render(
            **groups,
            site=self._config,
            **_link_context(""),
        )
        logger.debug("Rendered index with %d collection(s)", len(groups))
        return html

    def render_page(
        self,
        page: Page,
        collections: dict[str, list[Page]] | None = None,
    ) -> str:
        """Render a single content page with its declared template.

        Args:
            page: Page to render. ``page.template`` names the Jinja file.
            collections: Pages grouped by the top-level content directory
                that contains them. Each directory name is a template
                variable. Defaults to an empty mapping.

        Returns:
            Rendered page HTML.

        Raises:
            jinja2.TemplateNotFound: If ``page.template`` is missing.
        """
        groups = {} if collections is None else collections
        template = self._env.get_template(page.template)
        html = template.render(
            **groups,
            site=self._config,
            page=page,
            **_link_context(page.url),
        )
        logger.debug("Rendered page %s", page.url or page.slug)
        return html


def _root_prefix(url: str) -> str:
    """Return the relative prefix from a page URL back to the site root.

    Args:
        url: Site-relative HTML path. An empty string means the site root.

    Returns:
        ``""`` for a root page, ``"../"`` for one directory down, and so on.
    """
    parent = PurePosixPath(url).parent
    if parent == PurePosixPath("."):
        return ""
    return "../" * len(parent.parts)


def _link_context(url: str) -> dict[str, str]:
    """Build the template variables shared by every HTML page.

    Args:
        url: Site-relative path of the page being rendered. Empty for the
            homepage.

    Returns:
        ``home_url``, ``static_url``, and ``root_prefix``.
    """
    prefix = _root_prefix(url)
    return {
        "home_url": f"{prefix}index.html",
        "static_url": f"{prefix}static/",
        "root_prefix": prefix,
    }
