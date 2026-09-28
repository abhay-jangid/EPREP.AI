"""PySide6 desktop application lifecycle for EPREP.AI."""

import sys
from PySide6.QtWidgets import QApplication

from eprep import __app_name__, __version__
from eprep.ui.main_window import MainWindow
from eprep.ui.styles import DARK_THEME_STYLESHEET


def create_app(args: list[str] | None = None) -> QApplication:
    """Create or return the existing QApplication instance with dark theme applied."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(args if args is not None else sys.argv)
        app.setApplicationName(__app_name__)
        app.setApplicationDisplayName(__app_name__)
        app.setApplicationVersion(__version__)
        app.setStyleSheet(DARK_THEME_STYLESHEET)
    return app


def run_app() -> int:
    """Launch the EPREP.AI desktop application."""
    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec()
