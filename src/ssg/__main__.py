"""Allow ``python -m ssg`` as an entry point."""

from ssg.cli import main


def run() -> None:
    """Run the CLI when the package is executed as a module."""
    main()


if __name__ == "__main__":
    run()
