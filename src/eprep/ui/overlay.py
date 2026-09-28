"""Screen capture overlay widgets and multi-monitor capture session manager."""

from collections.abc import Callable
from PySide6.QtCore import QObject, QPoint, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPainterPath, QPen, QPixmap, QScreen
from PySide6.QtWidgets import QApplication, QWidget

from eprep.domain.exceptions import ScreenCaptureError
from eprep.infrastructure.imaging.capture import (
    clamp_rect_to_bounds,
    crop_pixmap_to_png_bytes,
    is_valid_selection,
    normalize_selection,
)


class CaptureOverlay(QWidget):
    """Frameless translucent overlay displayed over a single screen for region snipping."""

    region_selected = Signal(object, int, int, int, int)  # (QScreen, x, y, w, h)
    cancelled = Signal()

    def __init__(
        self,
        screen: QScreen,
        pixmap: QPixmap,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self._screen = screen
        self._pixmap = pixmap
        self._start_pos: QPoint | None = None
        self._current_pos: QPoint | None = None
        self._is_dragging: bool = False
        self._selection_rect = QRect()

        self._init_window()

    def _init_window(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setGeometry(self._screen.geometry())

    @property
    def screen_obj(self) -> QScreen:
        """The underlying screen object."""
        return self._screen

    @property
    def captured_pixmap(self) -> QPixmap:
        """The full screen captured pixmap."""
        return self._pixmap

    def clear_pixmap(self) -> None:
        """Release the backing desktop pixmap immediately to conserve memory."""
        self._pixmap = QPixmap()

    def enterEvent(self, event) -> None:  # noqa: N802
        """Ensure active overlay receives keyboard focus when hovered."""
        self.setFocus()
        super().enterEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Handle Escape key to cancel capture mode."""
        if event.key() == Qt.Key.Key_Escape:
            event.accept()
            self.cancelled.emit()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Begin rectangular region drag on left click; cancel on right click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.pos()
            self._current_pos = event.pos()
            self._selection_rect = QRect()
            self._is_dragging = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.cancelled.emit()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Update active drag coordinates and redraw the selection rectangle."""
        if self._is_dragging and self._start_pos is not None:
            self._current_pos = event.pos()
            nx, ny, nw, nh = normalize_selection(
                self._start_pos.x(),
                self._start_pos.y(),
                self._current_pos.x(),
                self._current_pos.y(),
            )
            cx, cy, cw, ch = clamp_rect_to_bounds(nx, ny, nw, nh, self.width(), self.height())
            self._selection_rect = QRect(cx, cy, cw, ch)
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Finish selection and emit region if valid, or reset if too small."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            if self._start_pos is not None:
                nx, ny, nw, nh = normalize_selection(
                    self._start_pos.x(),
                    self._start_pos.y(),
                    event.pos().x(),
                    event.pos().y(),
                )
                cx, cy, cw, ch = clamp_rect_to_bounds(nx, ny, nw, nh, self.width(), self.height())

                self._selection_rect = QRect()
                self._start_pos = None
                self._current_pos = None
                self.update()

                if is_valid_selection(cw, ch):
                    self.region_selected.emit(self._screen, cx, cy, cw, ch)

    def paintEvent(self, event) -> None:  # noqa: N802
        """Render captured desktop, dimming layer, clear selection cutout, and UI feedback."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Base desktop capture
        if not self._pixmap.isNull():
            painter.drawPixmap(self.rect(), self._pixmap)

        # 2. Dimming mask with clear cutout for the active selection
        dim_path = QPainterPath()
        dim_path.setFillRule(Qt.FillRule.OddEvenFill)
        dim_path.addRect(QRectF(self.rect()))

        has_selection = not self._selection_rect.isEmpty()
        if has_selection:
            dim_path.addRect(QRectF(self._selection_rect))

        # Translucent dark dimming
        painter.fillPath(dim_path, QColor(0, 0, 0, 110))

        # 3. Draw border and dimensions badge for active selection
        if has_selection:
            rect = self._selection_rect
            # Accent border (sky-400, 2px)
            pen = QPen(QColor("#38bdf8"), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)

            # Dimensions badge
            dim_text = f"{rect.width()} × {rect.height()}"
            badge_w = 84
            badge_h = 22
            badge_x = rect.x() + (rect.width() - badge_w) // 2
            # Place below if room, otherwise above
            badge_y = (
                rect.bottom() + 6 if rect.bottom() + 30 < self.height() else rect.top() - 28
            )
            badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(15, 23, 42, 220))
            painter.drawRoundedRect(badge_rect, 4, 4)

            painter.setPen(QColor("#f8fafc"))
            font = painter.font()
            font.setPointSize(9)
            font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, dim_text)

        # 4. Subtle instruction banner at top center
        instr_text = "Drag to select an area • Esc to cancel"
        font = painter.font()
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_w = metrics.horizontalAdvance(instr_text)
        instr_w = text_w + 32
        instr_h = 32
        instr_x = (self.width() - instr_w) // 2
        instr_y = 20
        instr_rect = QRect(instr_x, instr_y, instr_w, instr_h)

        painter.setPen(QPen(QColor("#334155"), 1))
        painter.setBrush(QColor(15, 23, 42, 220))
        painter.drawRoundedRect(instr_rect, 6, 6)

        painter.setPen(QColor("#cbd5e1"))
        painter.drawText(instr_rect, Qt.AlignmentFlag.AlignCenter, instr_text)


class CaptureManager(QObject):
    """Orchestrates screen capture sessions across single or multiple connected monitors."""

    DEFAULT_COMPOSITOR_SETTLE_MS: int = 35
    """Minimal fallback compositor settle duration in milliseconds on Windows.

    Why this exists:
        When a top-level Qt widget is hidden on Windows, Qt dispatches hide events and
        issues SW_HIDE to the underlying platform window. However, the Windows Desktop
        Window Manager (DWM) composes desktop surfaces asynchronously on its own render
        thread synchronized with display refresh intervals (e.g., ~16.6ms per frame at 60Hz).
        Windows does not expose a deterministic user-mode signal notifying applications
        when the DWM back-buffer has finished redrawing the vacated desktop surface.

        To prevent the application window from appearing as a ghost or artifact inside
        the desktop screen capture, a clean two-phase event-driven sequence is used:
        1. The window hide is requested, and execution is queued via QTimer.singleShot(0)
           so Qt processes all pending hide and platform window state events first.
        2. A minimal compositor settle duration (approx. 2 composition frames at 60Hz: ~33.3ms)
           is awaited via a non-blocking single-shot timer before capturing the screen.

    Caveat:
        This value represents a practical minimal verified timing on Windows rather than
        a universally guaranteed hardware guarantee across all display drivers and refresh rates.
    """

    capture_completed = Signal(bytes, str)  # (png_bytes, default_name)
    capture_cancelled = Signal()
    capture_failed = Signal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        grab_screen_fn: Callable[[QScreen], QPixmap] | None = None,
        screens_provider: Callable[[], list[QScreen]] | None = None,
        compositor_settle_ms: int = DEFAULT_COMPOSITOR_SETTLE_MS,
    ) -> None:
        super().__init__(parent)
        self._grab_screen_fn = grab_screen_fn or (lambda s: s.grabWindow(0))
        self._screens_provider = screens_provider or QApplication.screens
        self._compositor_settle_ms = max(0, compositor_settle_ms)
        self._overlays: list[CaptureOverlay] = []
        self._target_window: QWidget | None = None
        self._is_active: bool = False
        self._active_settle_ms: int = self._compositor_settle_ms

    @property
    def is_active(self) -> bool:
        """Return whether a capture session is currently active."""
        return self._is_active

    def start_capture(
        self,
        target_window: QWidget | None = None,
        settle_ms: int | None = None,
        delay_ms: int | None = None,
    ) -> bool:
        """Initiate screen capture mode using event-driven sequencing.

        Sequence:
            1. Re-entrancy guard check.
            2. Request target window hide (if visible).
            3. Queue execution to Qt event loop via QTimer.singleShot(0) to process hide events.
            4. Wait minimal DWM compositor settle interval before grabbing desktop.
            5. Acquire screen pixmaps and display snipping overlays.

        Args:
            target_window: The main application window to temporarily hide during capture.
            settle_ms: Settle interval in milliseconds (defaults to DEFAULT_COMPOSITOR_SETTLE_MS).
            delay_ms: Backwards-compatible alias for settle_ms.

        Returns:
            True if capture mode was successfully started, False if already active.
        """
        if self._is_active:
            return False

        self._is_active = True
        self._target_window = target_window

        if delay_ms is not None:
            active_settle = max(0, delay_ms)
        elif settle_ms is not None:
            active_settle = max(0, settle_ms)
        else:
            active_settle = self._compositor_settle_ms

        self._active_settle_ms = active_settle

        if self._target_window is not None and self._target_window.isVisible():
            self._target_window.hide()
            # Queue to Qt event loop: allows Qt to dispatch hide events and native window hide
            QTimer.singleShot(0, self._on_hide_processed)
        else:
            # Target window already hidden or not provided; proceed via queued Qt event loop
            if self._active_settle_ms > 0:
                QTimer.singleShot(self._active_settle_ms, self._acquire_and_show_overlays)
            else:
                QTimer.singleShot(0, self._acquire_and_show_overlays)

        return True

    def _on_hide_processed(self) -> None:
        """Invoked after Qt has processed the window hide event."""
        if not self._is_active:
            return

        if self._active_settle_ms > 0:
            QTimer.singleShot(self._active_settle_ms, self._acquire_and_show_overlays)
        else:
            self._acquire_and_show_overlays()

    def _acquire_and_show_overlays(self) -> None:
        """Grab all connected displays and show snipping overlays on each."""
        if not self._is_active:
            return

        try:
            screens = self._screens_provider()
            if not screens:
                raise ScreenCaptureError("No display screens found.")

            self._close_all_overlays()

            for screen in screens:
                pixmap = self._grab_screen_fn(screen)
                if pixmap.isNull():
                    raise ScreenCaptureError(f"Failed to grab screen '{screen.name()}'.")

                overlay = CaptureOverlay(screen, pixmap)
                overlay.region_selected.connect(self._on_region_selected)
                overlay.cancelled.connect(self._on_cancelled)
                overlay.show()
                overlay.activateWindow()
                self._overlays.append(overlay)

        except Exception as exc:
            self._cleanup_session()
            self.capture_failed.emit(str(exc))

    def _on_region_selected(
        self,
        screen: QScreen,
        x: int,
        y: int,
        w: int,
        h: int,
    ) -> None:
        """Handle region snipped on an overlay."""
        try:
            # Find the overlay matching the screen to extract its pixmap
            overlay = next((o for o in self._overlays if o.screen_obj == screen), None)
            if overlay is None or overlay.captured_pixmap.isNull():
                raise ScreenCaptureError("Screen capture pixmap is unavailable.")

            dpr = screen.devicePixelRatio()
            png_bytes = crop_pixmap_to_png_bytes(overlay.captured_pixmap, x, y, w, h, dpr)

            self._cleanup_session()
            self.capture_completed.emit(png_bytes, "Screen Capture")

        except Exception as exc:
            self._cleanup_session()
            self.capture_failed.emit(str(exc))

    def _on_cancelled(self) -> None:
        """Handle user cancellation via Escape or right-click."""
        self._cleanup_session()
        self.capture_cancelled.emit()

    def _cleanup_session(self) -> None:
        """Close all overlays, release backing pixmaps, and restore the main window."""
        self._close_all_overlays()
        self._restore_target_window()
        self._is_active = False

    def _close_all_overlays(self) -> None:
        """Close and delete all active capture overlay widgets."""
        for overlay in self._overlays:
            try:
                overlay.region_selected.disconnect()
                overlay.cancelled.disconnect()
            except RuntimeError:
                pass
            overlay.clear_pixmap()
            overlay.close()
            overlay.deleteLater()
        self._overlays.clear()

    def _restore_target_window(self) -> None:
        """Restore and activate the main application window."""
        if self._target_window is not None:
            self._target_window.show()
            self._target_window.raise_()
            self._target_window.activateWindow()
