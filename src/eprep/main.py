"""EPREP.AI application entry point foundation."""

import sys
from eprep import __app_name__, __version__


def main() -> int:
    """Application CLI entry point."""
    print(f"{__app_name__} v{__version__} - Foundation Initialized.")
    print("Application under active phase-by-phase development.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
