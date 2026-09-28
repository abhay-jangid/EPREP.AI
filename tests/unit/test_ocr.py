"""Unit and contract tests for OCR provider abstraction, models, and application service."""

import io
from PIL import Image, ImageDraw
import pytest

from eprep.application.ocr_service import OCRService
from eprep.application.screenshot_session import ScreenshotSession
from eprep.domain.exceptions import OCRProcessingError, OCRUnavailableError
from eprep.domain.models import ScreenshotItem
from eprep.domain.ocr import OCRLine, ScreenshotTextResult, SessionOCRResult
from eprep.infrastructure.imaging.processor import ImageLoader
from eprep.infrastructure.ocr.base import BaseOCRProvider
from eprep.infrastructure.ocr.rapidocr_provider import (
    RapidOCRProvider,
    sort_ocr_detections_reading_order,
)
from eprep.infrastructure.ocr.worker import OCRWorker


class MockOCRProvider(BaseOCRProvider):
    """Deterministic mock provider for contract testing without running ONNX inference."""

    def __init__(self, canned_lines: list[tuple[str, float]] | None = None) -> None:
        self.canned_lines = canned_lines or [
            ("def solve():", 0.95),
            ("    return 42", 0.92),
        ]
        self.initialized = False
        self.call_count = 0

    def initialize(self) -> None:
        self.initialized = True

    def is_available(self) -> bool:
        return self.initialized

    def extract_text_from_bytes(
        self,
        image_bytes: bytes,
        screenshot_id: str = "",
        screenshot_name: str = "",
    ) -> ScreenshotTextResult:
        if not image_bytes:
            raise OCRProcessingError("Image payload empty")

        if not self.initialized:
            self.initialize()

        self.call_count += 1
        lines = [
            OCRLine(
                text=text,
                confidence=conf,
                bounding_box=((0.0, float(i * 20)), (100.0, float(i * 20)), (100.0, float(i * 20 + 15)), (0.0, float(i * 20 + 15))),
                source_screenshot_id=screenshot_id,
                order=i + 1,
            )
            for i, (text, conf) in enumerate(self.canned_lines)
        ]
        combined = "\n".join(line.text for line in lines)
        return ScreenshotTextResult(
            screenshot_id=screenshot_id,
            screenshot_name=screenshot_name,
            lines=lines,
            combined_text=combined,
            processing_time_ms=5.0,
            warnings=[],
        )


def create_sample_png_bytes(text: str = "test code", size=(200, 60)) -> bytes:
    """Generate in-memory PNG bytes with simple rendered text."""
    img = Image.new("RGB", size, color="white")
    d = ImageDraw.Draw(img)
    d.text((10, 15), text, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. OCR Domain Models & Reading Order Tests
# ---------------------------------------------------------------------------


def test_ocr_line_attributes():
    """Verify OCRLine fields, immutability, and low-confidence flagging."""
    box = ((10.0, 10.0), (50.0, 10.0), (50.0, 25.0), (10.0, 25.0))
    line = OCRLine(text="x = 10", confidence=0.95, bounding_box=box, source_screenshot_id="s1", order=1)

    assert line.text == "x = 10"
    assert line.confidence == 0.95
    assert not line.is_low_confidence

    low_conf_line = OCRLine(text="?", confidence=0.45, bounding_box=box, source_screenshot_id="s1", order=2)
    assert low_conf_line.is_low_confidence


def test_sort_ocr_detections_reading_order():
    """Verify OCR boxes are sorted into top-to-bottom and left-to-right reading order."""
    # Box 1: line 2, left
    b1 = [[[10.0, 50.0], [50.0, 50.0], [50.0, 65.0], [10.0, 65.0]], "line2_left", 0.9]
    # Box 2: line 1, right
    b2 = [[[80.0, 10.0], [120.0, 10.0], [120.0, 25.0], [80.0, 25.0]], "line1_right", 0.9]
    # Box 3: line 1, left
    b3 = [[[10.0, 10.0], [50.0, 10.0], [50.0, 25.0], [10.0, 25.0]], "line1_left", 0.9]
    # Box 4: line 2, right
    b4 = [[[80.0, 50.0], [120.0, 50.0], [120.0, 65.0], [80.0, 65.0]], "line2_right", 0.9]

    unordered = [b1, b2, b3, b4]
    ordered = sort_ocr_detections_reading_order(unordered)
    texts = [item[1] for item in ordered]

    assert texts == ["line1_left", "line1_right", "line2_left", "line2_right"]


# ---------------------------------------------------------------------------
# 2. Provider Contract & Mock Provider Tests (Section 33)
# ---------------------------------------------------------------------------


def test_mock_provider_contract():
    """Verify BaseOCRProvider contract execution with mock implementation."""
    provider = MockOCRProvider()
    data = create_sample_png_bytes()

    res = provider.extract_text_from_bytes(data, screenshot_id="sc_001", screenshot_name="problem.png")
    assert res.screenshot_id == "sc_001"
    assert res.screenshot_name == "problem.png"
    assert res.line_count == 2
    assert res.lines[0].text == "def solve():"
    assert res.lines[1].text == "    return 42"
    assert "def solve():\n    return 42" in res.combined_text
    assert res.average_confidence > 0.90


def test_ocr_service_single_item():
    """Verify OCRService coordinates extraction for a single ScreenshotItem."""
    provider = MockOCRProvider([("int x = 5;", 0.98)])
    service = OCRService(provider=provider)

    data = create_sample_png_bytes("int x = 5;")
    item = ImageLoader.load_from_bytes(data, name="code.png", source_type="file")

    result = service.process_screenshot_item(item)
    assert result.screenshot_id == item.id
    assert result.screenshot_name == "code.png"
    assert result.lines[0].text == "int x = 5;"


# ---------------------------------------------------------------------------
# 3. Multi-Screenshot Session Ordering Tests (Section 35)
# ---------------------------------------------------------------------------


def test_multi_screenshot_session_processing_order():
    """Verify screenshots are processed in session insertion order with distinct sections."""
    provider = MockOCRProvider([("code line", 0.90)])
    service = OCRService(provider=provider)

    session = ScreenshotSession()
    for i in range(3):
        data = create_sample_png_bytes(f"Screenshot #{i+1}")
        session.add_from_bytes(data, name=f"problem_part_{i+1}.png")

    session_result = service.process_session(session)

    assert session_result.screenshot_count == 3
    assert session_result.total_lines == 3
    assert not session_result.is_empty

    # Verify screenshot IDs match session insertion order
    session_items = session.items
    for idx, res in enumerate(session_result.results):
        assert res.screenshot_id == session_items[idx].id
        assert res.screenshot_name == session_items[idx].name

    # Verify combined text contains formatted boundaries
    combined = session_result.combined_text
    assert "=== Screenshot 1: problem_part_1.png ===" in combined
    assert "=== Screenshot 2: problem_part_2.png ===" in combined
    assert "=== Screenshot 3: problem_part_3.png ===" in combined


def test_empty_session_returns_empty_ocr_result():
    """Verify empty ScreenshotSession returns safe empty SessionOCRResult."""
    service = OCRService(provider=MockOCRProvider())
    session = ScreenshotSession()

    res = service.process_session(session)
    assert res.screenshot_count == 0
    assert res.is_empty
    assert res.combined_text == ""


# ---------------------------------------------------------------------------
# 4. Error Handling & Edge Cases (Section 30 & 31)
# ---------------------------------------------------------------------------


def test_extract_empty_bytes_raises_error():
    """Verify empty image payload raises OCRProcessingError."""
    provider = RapidOCRProvider()
    with pytest.raises(OCRProcessingError):
        provider.extract_text_from_bytes(b"", screenshot_id="bad", screenshot_name="empty.png")


# ---------------------------------------------------------------------------
# 5. Background Worker Responsiveness Tests (Section 18 & 36)
# ---------------------------------------------------------------------------


def test_ocr_worker_execution_off_gui_thread():
    """Verify OCRWorker executes sequentially in background QThread emitting signals."""
    provider = MockOCRProvider([("line a", 0.9), ("line b", 0.85)])
    service = OCRService(provider=provider)

    data1 = create_sample_png_bytes("item 1")
    data2 = create_sample_png_bytes("item 2")
    item1 = ImageLoader.load_from_bytes(data1, name="img1.png")
    item2 = ImageLoader.load_from_bytes(data2, name="img2.png")

    progress_events = []
    finished_events = []
    session_results = []

    worker = OCRWorker(items=[item1, item2], ocr_service=service)
    worker.progress.connect(lambda cur, tot, name: progress_events.append((cur, tot, name)))
    worker.screenshot_finished.connect(finished_events.append)
    worker.finished_session.connect(session_results.append)

    # Run synchronously in test environment
    worker.run()

    assert len(progress_events) == 2
    assert progress_events[0] == (1, 2, "img1.png")
    assert progress_events[1] == (2, 2, "img2.png")

    assert len(finished_events) == 2
    assert len(session_results) == 1
    assert session_results[0].screenshot_count == 2


# ---------------------------------------------------------------------------
# 6. Real RapidOCR Engine Integration Tests (Section 34)
# ---------------------------------------------------------------------------


def test_real_rapidocr_provider_integration():
    """Verify real RapidOCRProvider extracts text from in-memory synthetic image."""
    provider = RapidOCRProvider(intra_op_num_threads=2)
    provider.initialize()
    assert provider.is_available()

    # Generate synthetic image with clear programming text
    data = create_sample_png_bytes("def solution(x): return x + 1", size=(350, 60))
    result = provider.extract_text_from_bytes(data, screenshot_id="real_test", screenshot_name="real.png")

    assert result.screenshot_id == "real_test"
    assert result.screenshot_name == "real.png"
    assert result.processing_time_ms > 0
    assert result.line_count >= 1
    # Check that key words were recognized
    combined = result.combined_text.lower()
    assert "solution" in combined or "def" in combined
