"""EPREP.AI application entry point."""

import sys
from eprep.ui.app import run_app


def main() -> int:
    """Launch EPREP.AI desktop application."""
    return run_app()


if __name__ == "__main__":
    sys.exit(main())
