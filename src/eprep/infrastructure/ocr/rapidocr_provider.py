"""RapidOCR provider implementation using ONNX Runtime for CPU inference."""

import logging
import time
from typing import Any

from eprep.domain.exceptions import OCRProcessingError, OCRUnavailableError
from eprep.domain.ocr import OCRLine, ScreenshotTextResult
from eprep.infrastructure.ocr.base import BaseOCRProvider

logger = logging.getLogger(__name__)


def sort_ocr_detections_reading_order(detections: list[Any]) -> list[Any]:
    """Sort OCR detection tuples into natural top-to-bottom, left-to-right reading order.

    Each detection tuple from RapidOCR is expected to be [box, text, score], where
    box is [[x1, y1], [x2, y2], [x3, y3], [x4, y4]].
    """
    if not detections:
        return []

    def get_metrics(item: Any) -> tuple[float, float, float, float]:
        box = item[0]
        ys = [float(p[1]) for p in box]
        xs = [float(p[0]) for p in box]
        min_y = min(ys)
        max_y = max(ys)
        min_x = min(xs)
        height = max(1.0, max_y - min_y)
        center_y = (min_y + max_y) / 2.0
        return min_y, min_x, center_y, height

    # Sort initially by top vertical coordinate
    sorted_by_y = sorted(detections, key=lambda item: get_metrics(item)[0])

    lines: list[list[Any]] = []
    for item in sorted_by_y:
        _, _, center_y, height = get_metrics(item)
        placed = False
        for line in lines:
            line_center_y = sum(get_metrics(i)[2] for i in line) / len(line)
            line_height = sum(get_metrics(i)[3] for i in line) / len(line)
            threshold = line_height * 0.5
            if abs(center_y - line_center_y) <= threshold:
                line.append(item)
                placed = True
                break
        if not placed:
            lines.append([item])

    # Sort each vertical cluster left-to-right
    ordered: list[Any] = []
    for line in lines:
        ordered.extend(sorted(line, key=lambda item: get_metrics(item)[1]))

    return ordered


class RapidOCRProvider(BaseOCRProvider):
    """Local-first OCR engine using RapidOCR and ONNX Runtime CPU.

    Optimized for low-power dual-core Windows execution (AMD Athlon Silver 3050U).
    """

    DEFAULT_INTRA_OP_THREADS: int = 2
    DEFAULT_INTER_OP_THREADS: int = 1

    def __init__(
        self,
        intra_op_num_threads: int = DEFAULT_INTRA_OP_THREADS,
        inter_op_num_threads: int = DEFAULT_INTER_OP_THREADS,
        text_score: float = 0.5,
    ) -> None:
        self._intra_op_num_threads = intra_op_num_threads
        self._inter_op_num_threads = inter_op_num_threads
        self._text_score = text_score
        self._engine: Any = None
        self._is_initialized = False

    def initialize(self) -> None:
        """Initialize the underlying RapidOCR engine and ONNX models."""
        if self._is_initialized and self._engine is not None:
            return

        try:
            from rapidocr_onnxruntime import RapidOCR

            logger.info("Initializing RapidOCR provider with intra_op=%d, inter_op=%d",
                        self._intra_op_num_threads, self._inter_op_num_threads)
            self._engine = RapidOCR(
                intra_op_num_threads=self._intra_op_num_threads,
                inter_op_num_threads=self._inter_op_num_threads,
                text_score=self._text_score,
            )
            self._is_initialized = True
            logger.info("RapidOCR provider initialized successfully.")
        except ImportError as exc:
            logger.error("RapidOCR import failed: %s", exc)
            raise OCRUnavailableError(
                f"RapidOCR engine is not installed or dependencies missing: {exc}"
            ) from exc
        except Exception as exc:
            logger.error("RapidOCR initialization failed: %s", exc)
            raise OCRUnavailableError(
                f"Failed to initialize RapidOCR models: {exc}"
            ) from exc

    def is_available(self) -> bool:
        """Return True if engine is loaded and available for inference."""
        return self._is_initialized and self._engine is not None

    def extract_text_from_bytes(
        self,
        image_bytes: bytes,
        screenshot_id: str = "",
        screenshot_name: str = "",
    ) -> ScreenshotTextResult:
        """Extract text from raw image bytes using RapidOCR without writing to disk."""
        if not image_bytes:
            raise OCRProcessingError("Cannot extract text from empty image payload.")

        if not self.is_available():
            self.initialize()

        logger.info("OCR started for screenshot '%s' (id=%s, bytes=%d)",
                    screenshot_name, screenshot_id, len(image_bytes))

        t_start = time.perf_counter()
        try:
            raw_result, _ = self._engine(image_bytes)
        except Exception as exc:
            logger.error("OCR inference error for screenshot '%s': %s", screenshot_name, exc)
            raise OCRProcessingError(f"RapidOCR inference failed: {exc}") from exc

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        logger.info("OCR completed for screenshot '%s' in %.2f ms", screenshot_name, elapsed_ms)

        if not raw_result:
            return ScreenshotTextResult(
                screenshot_id=screenshot_id,
                screenshot_name=screenshot_name,
                lines=[],
                combined_text="",
                processing_time_ms=elapsed_ms,
                warnings=[],
            )

        # Sort into deterministic reading order
        ordered_results = sort_ocr_detections_reading_order(raw_result)

        lines: list[OCRLine] = []
        warnings: list[str] = []

        for idx, item in enumerate(ordered_results, start=1):
            box, raw_text, score = item
            # Conservative normalization: trim trailing whitespace, keep internal punctuation intact
            clean_text = raw_text.strip()
            if not clean_text:
                continue

            # Convert 4-point polygon to immutable tuple of coordinate pairs
            box_tuple = tuple(
                (float(pt[0]), float(pt[1])) for pt in box
            )

            ocr_line = OCRLine(
                text=clean_text,
                confidence=float(score),
                bounding_box=box_tuple,
                source_screenshot_id=screenshot_id,
                order=idx,
            )
            lines.append(ocr_line)

            if ocr_line.is_low_confidence:
                warnings.append(f"Line {idx} has low confidence ({score:.2f})")

        combined_text = "\n".join(line.text for line in lines)

        return ScreenshotTextResult(
            screenshot_id=screenshot_id,
            screenshot_name=screenshot_name,
            lines=lines,
            combined_text=combined_text,
            processing_time_ms=elapsed_ms,
            warnings=warnings,
        )
