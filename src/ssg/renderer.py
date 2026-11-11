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

    def render_index(self, posts: list[Page], pages: list[Page] | None = None) -> str:
        """Render the homepage with a list of posts.

        Args:
            posts: Posts passed to the ``index.html`` template as ``posts``.
            pages: Root content pages passed to every template as ``pages``.
                Used for the site navigation. Defaults to an empty list.

        Returns:
            Rendered homepage HTML.

        Raises:
            jinja2.TemplateNotFound: If ``index.html`` is missing.
        """
        template = self._env.get_template("index.html")
        html = template.render(
            site=self._config,
            posts=posts,
            **_link_context("", pages),
        )
        logger.debug("Rendered index with %d post(s)", len(posts))
        return html

    def render_post(self, page: Page, pages: list[Page] | None = None) -> str:
        """Render a single content page.

        Args:
            page: Page passed to the ``post.html`` template.
            pages: Root content pages passed to every template as ``pages``.
                Used for the site navigation. Defaults to an empty list.

        Returns:
            Rendered page HTML.

        Raises:
            jinja2.TemplateNotFound: If ``post.html`` is missing.
        """
        template = self._env.get_template("post.html")
        html = template.render(
            site=self._config,
            page=page,
            **_link_context(page.url, pages),
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


def _link_context(url: str, pages: list[Page] | None) -> dict[str, object]:
    """Build the template variables shared by every HTML page.

    Args:
        url: Site-relative path of the page being rendered. Empty for the
            homepage.
        pages: Root content pages linked from the navigation.

    Returns:
        ``pages``, ``home_url``, ``static_url``, and ``root_prefix``.
    """
    prefix = _root_prefix(url)
    return {
        "pages": [] if pages is None else pages,
        "home_url": f"{prefix}index.html",
        "static_url": f"{prefix}static/",
        "root_prefix": prefix,
    }
