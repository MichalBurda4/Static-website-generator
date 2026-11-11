"""CLI entry point for the static site generator."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from pathlib import Path

from ssg import __version__
from ssg.builder import SiteBuilder
from ssg.config import SiteConfig, load_config
from ssg.parser import Page, load_pages

logger = logging.getLogger(__name__)

CommandHandler = Callable[[SiteConfig], None]


def _configure_stdout() -> None:
    """Force UTF-8 on Windows so non-ASCII characters do not crash the CLI."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # pyright: ignore


def _configure_logging() -> None:
    """Configure application logging for library modules."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _add_config_argument(parser: argparse.ArgumentParser) -> None:
    """Add the shared ``--config`` option to a subcommand parser.

    Args:
        parser: Subcommand parser that receives the option.
    """
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to the configuration file (default: config.yaml)",
    )


def _configure_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with ``parse`` and ``build`` commands.

    Returns:
        A parser that accepts ``--version``, ``parse``, and ``build``.
    """
    parser = argparse.ArgumentParser(description="Simple static site generator")
    parser.add_argument("--version", action="version", version=f"ssg {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    parse_cmd = subparsers.add_parser(
        "parse",
        help="Load and print parsed Markdown files",
    )
    _add_config_argument(parse_cmd)

    build_cmd = subparsers.add_parser(
        "build",
        help="Generate HTML pages into the output directory",
    )
    _add_config_argument(build_cmd)

    return parser


def _print_page(page: Page) -> None:
    """Print one parsed page summary for the user.

    Args:
        page: Page whose title, date, slug, path, and HTML snippet are printed.
    """
    date_str = page.date.isoformat() if page.date else "no date"
    snippet = page.html[:80].replace("\n", " ")
    print(f"- {page.title} ({date_str}) [{page.slug}]")
    print(f"  url: {page.url}")
    print(f"  file: {page.source_path}")
    print(f"  HTML: {snippet}...")
    print()


def _cmd_parse(config: SiteConfig) -> None:
    """Handle the ``parse`` command and print results to the user.

    Args:
        config: Loaded site configuration.

    Raises:
        FileNotFoundError: If the content directory does not exist.
        TypeError: If a page's front matter is not a YAML mapping.
        ValueError: If a page's date is not a supported format.
        yaml.YAMLError: If a page's front matter is not valid YAML.
    """
    pages = load_pages(config.content_path)
    if not pages:
        print(f"No Markdown files in: {config.content_path}")
        return

    print(f"Site: {config.site_name}")
    print(f"Pages found: {len(pages)}\n")
    for page in pages:
        _print_page(page)


def _cmd_build(config: SiteConfig) -> None:
    """Handle the ``build`` command and print a short build summary.

    Args:
        config: Loaded site configuration.

    Raises:
        FileNotFoundError: If the content directory does not exist.
        jinja2.TemplateNotFound: If a required template is missing.
        TypeError: If a page's front matter is not a YAML mapping.
        ValueError: If a page's date is not a supported format.
        yaml.YAMLError: If a page's front matter is not valid YAML.
    """
    result = SiteBuilder(config).build()

    print(f"Built {len(result.html_files)} HTML file(s) into: {config.output_path}")
    for path in result.html_files:
        print(f"  - {path.relative_to(config.output_path)}")

    static_dir = config.output_path / "static"
    print(f"Copied {len(result.static_files)} static file(s) into: {static_dir}")
    for path in result.static_files:
        print(f"  - {path.relative_to(static_dir)}")


def _command_handlers() -> dict[str, CommandHandler]:
    """Return the mapping of CLI command names to handlers.

    Returns:
        Handlers for the ``parse`` and ``build`` commands.
    """
    return {
        "parse": _cmd_parse,
        "build": _cmd_build,
    }


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments and dispatch the selected command.

    Args:
        argv: Arguments to parse, excluding the program name. When omitted,
            ``argparse`` reads ``sys.argv``.

    Raises:
        SystemExit: If the arguments are invalid or ``--version`` is passed.
        FileNotFoundError: If the configuration file or content directory
            does not exist.
        TypeError: If configuration or front matter is not a YAML mapping.
        ValueError: If configuration fields are missing or a page date is
            invalid.
        yaml.YAMLError: If a YAML file is not valid.
        jinja2.TemplateNotFound: If ``build`` cannot find a template.
    """
    _configure_stdout()
    _configure_logging()

    parser = _configure_parser()
    args = parser.parse_args(argv)
    handler = _command_handlers().get(args.command)

    if handler is None:
        parser.print_help()
        return

    logger.debug("Running command: %s", args.command)
    handler(load_config(args.config))


if __name__ == "__main__":
    main()
