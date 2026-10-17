"""Tymczasowy punkt wejścia CLI — pełne komendy w kolejnych etapach."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ssg import __version__
from ssg.config import load_config
from ssg.parser import load_pages


def _configure_stdout() -> None:
    """Ustaw UTF-8 na Windows, żeby polskie znaki nie wywalały CLI."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # pyright: ignore


def main(argv: list[str] | None = None) -> None:
    _configure_stdout()
    parser = argparse.ArgumentParser(description="Prosty Static Site Generator")
    parser.add_argument("--version", action="version", version=f"ssg {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    parse_cmd = subparsers.add_parser(
        "parse",
        help="Wczytaj i wypisz sparsowane pliki Markdown (punkt 2 projektu)",
    )
    parse_cmd.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Ścieżka do pliku konfiguracji (domyślnie: config.yaml)",
    )

    args = parser.parse_args(argv)

    if args.command == "parse":
        config = load_config(args.config)
        pages = load_pages(config.content_path)
        if not pages:
            print(f"Brak plików Markdown w: {config.content_path}")
            return

        print(f"Strona: {config.site_name}")
        print(f"Znaleziono stron: {len(pages)}\n")
        for page in pages:
            date_str = page.date.isoformat() if page.date else "brak daty"
            print(f"- {page.title} ({date_str}) [{page.slug}]")
            print(f"  plik: {page.source_path}")
            snippet = page.html[:80].replace("\n", " ")
            print(f"  HTML: {snippet}...")
            print()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
