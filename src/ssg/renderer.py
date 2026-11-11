"""Render HTML pages with Jinja2 templates."""

from __future__ import annotations

import logging

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

    def render_index(self, pages: list[Page]) -> str:
        """Render the homepage with a list of posts.

        Args:
            pages: Pages passed to the ``index.html`` template.

        Returns:
            Rendered homepage HTML.

        Raises:
            jinja2.TemplateNotFound: If ``index.html`` is missing.
        """
        template = self._env.get_template("index.html")
        html = template.render(
            site=self._config,
            pages=pages,
            home_url="index.html",
            static_url="static/",
        )
        logger.debug("Rendered index with %d page(s)", len(pages))
        return html

    def render_post(self, page: Page) -> str:
        """Render a single post page.

        Args:
            page: Page passed to the ``post.html`` template.

        Returns:
            Rendered post HTML.

        Raises:
            jinja2.TemplateNotFound: If ``post.html`` is missing.
        """
        template = self._env.get_template("post.html")
        html = template.render(
            site=self._config,
            page=page,
            home_url="index.html",
            static_url="static/",
        )
        logger.debug("Rendered post %s", page.slug)
        return html
