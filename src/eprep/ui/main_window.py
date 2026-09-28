"""Main window shell for EPREP.AI desktop application."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from eprep import __app_name__
from eprep.ui.widgets.language_selector import LanguageSelector
from eprep.ui.widgets.screenshot_panel import ScreenshotPanel
from eprep.ui.widgets.solution_panel import SolutionPanel


class MainWindow(QMainWindow):
    """Primary application window for EPREP.AI."""

    DEFAULT_WIDTH = 1000
    DEFAULT_HEIGHT = 680
    MIN_WIDTH = 800
    MIN_HEIGHT = 540

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_window()
        self._init_ui()

    def _init_window(self) -> None:
        self.setWindowTitle(__app_name__)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(14, 12, 14, 10)
        root_layout.setSpacing(10)

        # 1. Header Area
        header_widget = self._create_header()
        root_layout.addWidget(header_widget)

        # 2. Main Workspace (Splitter between Screenshot Panel & Solution Panel)
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._screenshot_panel = ScreenshotPanel(self._splitter)
        self._solution_panel = SolutionPanel(self._splitter)

        self._splitter.addWidget(self._screenshot_panel)
        self._splitter.addWidget(self._solution_panel)
        self._splitter.setStretchFactor(0, 4)
        self._splitter.setStretchFactor(1, 6)

        root_layout.addWidget(self._splitter, 1)

        # 3. Action and Control Bar
        control_bar = self._create_control_bar()
        root_layout.addWidget(control_bar)

        # 4. Status Bar
        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        # Connect signals
        self._screenshot_panel.status_message_emitted.connect(self._status_bar.showMessage)

    def _create_header(self) -> QWidget:
        header = QFrame(self)
        header.setFrameShape(QFrame.Shape.NoFrame)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(4, 2, 4, 6)

        # Branding
        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        app_title = QLabel(__app_name__, header)
        app_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f8fafc;")

        app_subtitle = QLabel("Local AI Coding Assistant", header)
        app_subtitle.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 500;")

        title_box.addWidget(app_title)
        title_box.addWidget(app_subtitle)
        layout.addLayout(title_box)

        layout.addStretch()

        # Language Selector
        self._language_selector = LanguageSelector(header)
        layout.addWidget(self._language_selector)

        return header

    def _create_control_bar(self) -> QWidget:
        bar = QFrame(self)
        bar.setFrameShape(QFrame.Shape.StyledPanel)
        bar.setStyleSheet(
            "QFrame { background-color: #1e293b; border: 1px solid #334155; "
            "border-radius: 6px; padding: 4px; }"
        )

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(16)

        # Output Mode display (locked default: Safe Paste)
        self._output_mode_label = QLabel("Output Mode: Safe Paste", bar)
        self._output_mode_label.setStyleSheet(
            "color: #cbd5e1; font-size: 12px; font-weight: 500; "
            "background-color: #0f172a; border: 1px solid #334155; "
            "border-radius: 4px; padding: 3px 8px;"
        )

        # Typing Status display
        self._typing_status_label = QLabel("Typing: Not Ready to Type", bar)
        self._typing_status_label.setStyleSheet(
            "color: #64748b; font-size: 12px; font-weight: 500; font-style: italic;"
        )

        layout.addWidget(self._output_mode_label)
        layout.addWidget(self._typing_status_label)
        layout.addStretch()

        # Analyze Problem action button (disabled initially)
        self._analyze_btn = QPushButton("Analyze Problem", bar)
        self._analyze_btn.setEnabled(False)
        self._analyze_btn.setToolTip("Will be enabled when screenshots are added and AI integration is connected")
        self._analyze_btn.setStyleSheet(
            "QPushButton { font-weight: 600; padding: 6px 18px; }"
        )
        layout.addWidget(self._analyze_btn)

        return bar

    @property
    def language_selector(self) -> LanguageSelector:
        """Return the language selector widget."""
        return self._language_selector

    @property
    def screenshot_panel(self) -> ScreenshotPanel:
        """Return the screenshot panel widget."""
        return self._screenshot_panel

    @property
    def solution_panel(self) -> SolutionPanel:
        """Return the solution panel widget."""
        return self._solution_panel

    @property
    def analyze_button(self) -> QPushButton:
        """Return the analyze problem button."""
        return self._analyze_btn

    @property
    def output_mode_label(self) -> QLabel:
        """Return the output mode label."""
        return self._output_mode_label

    @property
    def typing_status_label(self) -> QLabel:
        """Return the typing status label."""
        return self._typing_status_label
