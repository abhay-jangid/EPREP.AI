"""Application service orchestrating OCR extraction across session screenshots."""

import time

from eprep.application.screenshot_session import ScreenshotSession
from eprep.domain.models import ScreenshotItem
from eprep.domain.ocr import ScreenshotTextResult, SessionOCRResult
from eprep.infrastructure.ocr.base import BaseOCRProvider
from eprep.infrastructure.ocr.rapidocr_provider import RapidOCRProvider


class OCRService:
    """Application coordinator for local OCR text extraction from problem screenshots."""

    def __init__(self, provider: BaseOCRProvider | None = None) -> None:
        self._provider = provider or RapidOCRProvider()

    @property
    def provider(self) -> BaseOCRProvider:
        """Return the active OCR provider."""
        return self._provider

    def process_screenshot_item(self, item: ScreenshotItem) -> ScreenshotTextResult:
        """Extract text from an individual in-memory ScreenshotItem."""
        return self._provider.extract_text_from_bytes(
            image_bytes=item.image_bytes,
            screenshot_id=item.id,
            screenshot_name=item.name,
        )

    def process_session(self, session: ScreenshotSession) -> SessionOCRResult:
        """Extract text sequentially from all screenshots in the active session.

        Preserves session insertion order and associates results with each source screenshot.
        """
        if session.is_empty:
            return SessionOCRResult(results=[], total_time_ms=0.0)

        t_start = time.perf_counter()
        results: list[ScreenshotTextResult] = []

        for item in session.items:
            res = self.process_screenshot_item(item)
            results.append(res)

        total_time_ms = (time.perf_counter() - t_start) * 1000.0
        return SessionOCRResult(results=results, total_time_ms=total_time_ms)
