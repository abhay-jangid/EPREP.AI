"""PySide6 desktop application lifecycle for EPREP.AI."""

import sys
from PySide6.QtWidgets import QApplication

from eprep import __app_name__, __version__
from eprep.ui.main_window import MainWindow


def create_app(args: list[str] | None = None) -> QApplication:
    """Create or return the existing QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(args if args is not None else sys.argv)
        app.setApplicationName(__app_name__)
        app.setApplicationDisplayName(__app_name__)
        app.setApplicationVersion(__version__)
    return app


def run_app() -> int:
    """Launch the EPREP.AI desktop application."""
    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec()
