"""Render HTML pages with Jinja2 templates."""

from __future__ import annotations

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ssg.config import SiteConfig
from ssg.parser import Page


class Renderer:
    """Load templates from disk and render pages / the homepage."""

    def __init__(self, config: SiteConfig) -> None:
        self._config = config
        self._env = Environment(
            loader=FileSystemLoader(str(config.templates_path)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_index(self, pages: list[Page]) -> str:
        """Render the homepage with a list of posts."""
        template = self._env.get_template("index.html")
        return template.render(
            site=self._config,
            pages=pages,
            home_url="index.html",
            static_url="static/",
        )

    def render_post(self, page: Page) -> str:
        """Render a single post page."""
        template = self._env.get_template("post.html")
        return template.render(
            site=self._config,
            page=page,
            home_url="index.html",
            static_url="static/",
        )
