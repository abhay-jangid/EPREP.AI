from __future__ import annotations
import time
from typing import TYPE_CHECKING
from PySide6.QtCore import QThread, Signal

from eprep.domain.models import ScreenshotItem
from eprep.domain.ocr import ScreenshotTextResult, SessionOCRResult

if TYPE_CHECKING:
    from eprep.application.ocr_service import OCRService


class OCRWorker(QThread):
    """Executes OCR extraction sequentially across screenshots off the Qt GUI thread."""

    progress = Signal(int, int, str)  # (current 1-based index, total_count, screenshot_name)
    screenshot_finished = Signal(object)  # (ScreenshotTextResult)
    finished_session = Signal(object)  # (SessionOCRResult)
    failed = Signal(str)  # (error_message)

    def __init__(
        self,
        items: list[ScreenshotItem],
        ocr_service: OCRService | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._items = list(items)
        if ocr_service is None:
            from eprep.application.ocr_service import OCRService
            self._ocr_service = OCRService()
        else:
            self._ocr_service = ocr_service

    def run(self) -> None:
        """Execute OCR extraction for all items in insertion order without blocking GUI."""
        if not self._items:
            self.finished_session.emit(SessionOCRResult(results=[], total_time_ms=0.0))
            return

        t_start = time.perf_counter()
        results: list[ScreenshotTextResult] = []
        total = len(self._items)

        try:
            for idx, item in enumerate(self._items, start=1):
                self.progress.emit(idx, total, item.name)
                res = self._ocr_service.process_screenshot_item(item)
                results.append(res)
                self.screenshot_finished.emit(res)

            total_ms = (time.perf_counter() - t_start) * 1000.0
            session_result = SessionOCRResult(results=results, total_time_ms=total_ms)
            self.finished_session.emit(session_result)
        except Exception as exc:
            self.failed.emit(str(exc))
