"""Screenshot management panel widget with file upload, drag-and-drop, and preview."""

from pathlib import Path
from PySide6.QtCore import QBuffer, QIODevice, Qt, Signal
from PySide6.QtGui import QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from eprep.application.screenshot_session import ScreenshotSession
from eprep.domain.exceptions import EprepError
from eprep.domain.models import ScreenshotItem


class ScreenshotCard(QFrame):
    """Visual card displaying a single in-memory screenshot thumbnail with remove action."""

    remove_requested = Signal(str)

    def __init__(self, item: ScreenshotItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.item_id = item.id
        self._init_ui(item)

    def _init_ui(self, item: ScreenshotItem) -> None:
        self.setObjectName("ScreenshotCard")
        self.setStyleSheet(
            "#ScreenshotCard { background-color: #162032; border: 1px solid #334155; "
            "border-radius: 8px; } "
            "QLabel { border: none; background: transparent; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # 1. Thumbnail Image
        self._thumbnail_label = QLabel(self)
        self._thumbnail_label.setFixedSize(68, 68)
        self._thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumbnail_label.setStyleSheet(
            "QLabel { background-color: #090d16; border: 1px solid #334155; border-radius: 6px; }"
        )

        qimg = QImage.fromData(item.image_bytes)
        if not qimg.isNull():
            pixmap = QPixmap.fromImage(qimg).scaled(
                64,
                64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._thumbnail_label.setPixmap(pixmap)

        layout.addWidget(self._thumbnail_label)

        # 2. Metadata / Details
        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(4)
        meta_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        display_name = item.name
        if len(display_name) > 24:
            display_name = display_name[:12] + "..." + display_name[-9:]

        name_label = QLabel(display_name, self)
        name_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #f8fafc; border: none;")
        name_label.setToolTip(item.name)

        dim_label = QLabel(f"{item.width} × {item.height} ({item.format})", self)
        dim_label.setStyleSheet("font-size: 11px; color: #94a3b8; border: none;")

        meta_layout.addWidget(name_label)
        meta_layout.addWidget(dim_label)
        layout.addLayout(meta_layout, 1)

        # 3. Remove Button
        remove_btn = QPushButton("✕", self)
        remove_btn.setFixedSize(28, 28)
        remove_btn.setToolTip("Remove screenshot")
        remove_btn.setStyleSheet(
            "QPushButton { background-color: #1e293b; color: #cbd5e1; border: 1px solid #475569; "
            "border-radius: 14px; font-size: 12px; font-weight: bold; padding: 0px; text-align: center; } "
            "QPushButton:hover { background-color: #dc2626; color: #ffffff; border-color: #ef4444; }"
        )
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.item_id))
        layout.addWidget(remove_btn)


class ScreenshotPanel(QWidget):
    """Panel displaying screenshot list, thumbnail previews, and upload/drop controls."""

    status_message_emitted = Signal(str)
    session_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = ScreenshotSession()
        self.setAcceptDrops(True)
        self._init_ui()
        self._refresh_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header with title and count
        header_layout = QHBoxLayout()
        self._title_label = QLabel("Screenshots", self)
        self._title_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #f1f5f9;")

        self._count_label = QLabel(f"0 / {self._session.MAX_SCREENSHOTS}", self)
        self._count_label.setStyleSheet(
            "background-color: #1e293b; color: #cbd5e1; border: 1px solid #334155; "
            "font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 10px;"
        )

        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        header_layout.addWidget(self._count_label)
        main_layout.addLayout(header_layout)

        # Stacked display: Empty state vs Scrollable thumbnails
        self._stack = QStackedWidget(self)

        # 1. Empty state view
        self._empty_frame = QFrame(self._stack)
        self._empty_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self._empty_frame.setStyleSheet(
            "QFrame { border: 2px dashed #334155; border-radius: 8px; background-color: #0b0f19; }"
        )

        empty_layout = QVBoxLayout(self._empty_frame)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._empty_label = QLabel(
            "No screenshots added\n\nUpload, drop, or paste (Ctrl+V) up to 5 screenshots.",
            self._empty_frame,
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.4;")
        empty_layout.addWidget(self._empty_label)

        self._stack.addWidget(self._empty_frame)

        # 2. Scrollable thumbnails view
        self._scroll_area = QScrollArea(self._stack)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet(
            "QScrollArea { border: 1px solid #334155; border-radius: 8px; background-color: #0b0f19; } "
            "QScrollBar:vertical { background-color: #0b0f19; width: 8px; margin: 0; } "
            "QScrollBar::handle:vertical { background-color: #334155; border-radius: 4px; min-height: 20px; } "
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        self._cards_container = QWidget(self._scroll_area)
        self._cards_container.setStyleSheet("background-color: #0b0f19;")
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(6, 6, 6, 6)
        self._cards_layout.setSpacing(6)
        self._cards_layout.addStretch()

        self._scroll_area.setWidget(self._cards_container)
        self._stack.addWidget(self._scroll_area)

        main_layout.addWidget(self._stack, 1)

        # Bottom Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self._add_btn = QPushButton("Add Screenshot", self)
        self._add_btn.setToolTip("Select image files to upload")
        self._add_btn.clicked.connect(self._on_add_clicked)

        self._capture_btn = QPushButton("Capture Screen", self)
        self._capture_btn.setEnabled(False)
        self._capture_btn.setToolTip("Screen snipping will be available in Phase 5")

        self._clear_btn = QPushButton("Clear", self)
        self._clear_btn.setEnabled(False)
        self._clear_btn.setToolTip("Clear all screenshots from current session")
        self._clear_btn.clicked.connect(self._on_clear_clicked)

        button_layout.addWidget(self._add_btn)
        button_layout.addWidget(self._capture_btn)
        button_layout.addWidget(self._clear_btn)
        main_layout.addLayout(button_layout)

    def _refresh_ui(self) -> None:
        """Synchronize the UI with the current session state."""
        count = self._session.count
        self._count_label.setText(f"{count} / {self._session.MAX_SCREENSHOTS}")

        # Update button states
        self._add_btn.setEnabled(not self._session.is_full)
        self._capture_btn.setEnabled(False)  # Strictly Phase 5
        self._clear_btn.setEnabled(count > 0)

        # Clear existing card widgets
        while self._cards_layout.count() > 1:
            child = self._cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if self._session.is_empty:
            self._stack.setCurrentWidget(self._empty_frame)
        else:
            self._stack.setCurrentWidget(self._scroll_area)
            # Re-populate cards preserving insertion order
            for item in self._session.items:
                card = ScreenshotCard(item, self._cards_container)
                card.remove_requested.connect(self._on_remove_clicked)
                self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

        self.session_changed.emit(count)

    def _on_add_clicked(self) -> None:
        """Handle Add Screenshot button click via file dialog."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Screenshots",
            "",
            "Images (*.png *.jpg *.jpeg *.webp);;All Files (*)",
        )
        if file_paths:
            self.add_paths(file_paths)

    def add_paths(self, file_paths: list[str | Path]) -> None:
        """Add multiple file paths to the screenshot session."""
        result = self._session.add_multiple_paths(file_paths)
        self._refresh_ui()
        self.status_message_emitted.emit(result.status_message)

    def _on_remove_clicked(self, item_id: str) -> None:
        """Handle removal of an individual screenshot."""
        if self._session.remove_item(item_id):
            self._refresh_ui()
            self.status_message_emitted.emit("Screenshot removed.")

    def _on_clear_clicked(self) -> None:
        """Clear all screenshots from current session."""
        self._session.clear()
        self._refresh_ui()
        self.status_message_emitted.emit("Screenshots cleared.")

    def _handle_paste(self) -> bool:
        """Attempt to paste an image from the Windows clipboard into the session."""
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return False

        qimg = clipboard.image()
        if qimg.isNull():
            return False

        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not qimg.save(buffer, "PNG"):
            return False

        png_bytes = bytes(buffer.data())
        name = f"Pasted Screenshot {self._session.count + 1}.png"

        try:
            self._session.add_from_bytes(png_bytes, name=name, source_type="paste")
            self._refresh_ui()
            self.status_message_emitted.emit("Pasted screenshot added.")
            return True
        except EprepError as exc:
            self.status_message_emitted.emit(str(exc))
            return False

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Support pasting image screenshots via Ctrl+V shortcut."""
        if event.matches(QKeySequence.StandardKey.Paste):
            if self._handle_paste():
                event.accept()
                return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        """Accept drag events containing file URLs."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # noqa: N802
        """Handle dropped files."""
        urls = event.mimeData().urls()
        file_paths: list[str] = [url.toLocalFile() for url in urls if url.isLocalFile()]

        if file_paths:
            event.acceptProposedAction()
            self.add_paths(file_paths)
        else:
            event.ignore()

    # Public inspection properties for testing
    @property
    def session(self) -> ScreenshotSession:
        """Return the active screenshot session."""
        return self._session

    @property
    def count_label_text(self) -> str:
        """Return the count label text."""
        return self._count_label.text()

    @property
    def is_empty(self) -> bool:
        """Check if screenshot panel is empty."""
        return self._session.is_empty

    @property
    def add_button(self) -> QPushButton:
        """Return the add screenshot button."""
        return self._add_btn

    @property
    def capture_button(self) -> QPushButton:
        """Return the capture screen button."""
        return self._capture_btn

    @property
    def clear_button(self) -> QPushButton:
        """Return the clear button."""
        return self._clear_btn
