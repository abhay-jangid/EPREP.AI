"""Abstract base provider interface for OCR engines."""

from abc import ABC, abstractmethod

from eprep.domain.ocr import ScreenshotTextResult


class BaseOCRProvider(ABC):
    """Abstract contract for all local OCR text extraction engines."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the OCR engine and load models into memory."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the OCR engine and its required models are ready for inference."""

    @abstractmethod
    def extract_text_from_bytes(
        self,
        image_bytes: bytes,
        screenshot_id: str = "",
        screenshot_name: str = "",
    ) -> ScreenshotTextResult:
        """Extract text from raw in-memory image bytes.

        Args:
            image_bytes: Authoritative in-memory image payload.
            screenshot_id: Unique identifier of the source screenshot item.
            screenshot_name: Display name of the source screenshot item.

        Returns:
            Structured ScreenshotTextResult containing recognized lines, confidence, and boxes.

        Raises:
            OCRUnavailableError: If the OCR engine is not installed or cannot initialize.
            OCRProcessingError: If an error occurs during inference or decoding.
        """
