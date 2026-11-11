"""Allow ``python -m ssg`` as an entry point."""

from ssg.cli import main


def run() -> None:
    """Run the CLI when the package is executed as a module.

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
    main()


if __name__ == "__main__":
    run()
