"""CLI entry point for the static site generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ssg import __version__
from ssg.builder import SiteBuilder
from ssg.config import load_config
from ssg.parser import load_pages


def _configure_stdout() -> None:
    """Force UTF-8 on Windows so non-ASCII characters do not crash the CLI."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # pyright: ignore


def _add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to the configuration file (default: config.yaml)",
    )


def main(argv: list[str] | None = None) -> None:
    _configure_stdout()
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

    args = parser.parse_args(argv)

    if args.command == "parse":
        config = load_config(args.config)
        pages = load_pages(config.content_path)
        if not pages:
            print(f"No Markdown files in: {config.content_path}")
            return

        print(f"Site: {config.site_name}")
        print(f"Pages found: {len(pages)}\n")
        for page in pages:
            date_str = page.date.isoformat() if page.date else "no date"
            print(f"- {page.title} ({date_str}) [{page.slug}]")
            print(f"  file: {page.source_path}")
            snippet = page.html[:80].replace("\n", " ")
            print(f"  HTML: {snippet}...")
            print()
        return

    if args.command == "build":
        config = load_config(args.config)
        written = SiteBuilder(config).build()
        print(f"Built {len(written)} HTML file(s) into: {config.output_path}")
        for path in written:
            print(f"  - {path.name}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
