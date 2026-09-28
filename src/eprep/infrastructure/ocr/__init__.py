"""OCR infrastructure package for local text extraction."""

from eprep.infrastructure.ocr.base import BaseOCRProvider
from eprep.infrastructure.ocr.rapidocr_provider import (
    RapidOCRProvider,
    sort_ocr_detections_reading_order,
)

__all__ = [
    "BaseOCRProvider",
    "RapidOCRProvider",
    "sort_ocr_detections_reading_order",
]


