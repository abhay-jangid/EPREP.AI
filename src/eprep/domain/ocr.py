"""Domain models for OCR text extraction and structured screenshot understanding."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OCRLine:
    """Represents a single recognized line of text with position and confidence."""

    text: str
    confidence: float
    bounding_box: tuple[tuple[float, float], ...]  # 4 corner points ((x,y), ...)
    source_screenshot_id: str = ""
    order: int = 0

    @property
    def is_low_confidence(self) -> bool:
        """Flag whether line confidence is below recommended threshold (0.60)."""
        return self.confidence < 0.60


@dataclass
class ScreenshotTextResult:
    """Structured OCR extraction result for a single screenshot item."""

    screenshot_id: str
    screenshot_name: str
    lines: list[OCRLine] = field(default_factory=list)
    combined_text: str = ""
    processing_time_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        """Total number of recognized lines in this screenshot."""
        return len(self.lines)

    @property
    def average_confidence(self) -> float:
        """Average confidence across all recognized lines, or 0.0 if empty."""
        if not self.lines:
            return 0.0
        return sum(line.confidence for line in self.lines) / len(self.lines)


@dataclass
class SessionOCRResult:
    """Aggregated OCR results across all screenshots in a session, preserving insertion order."""

    results: list[ScreenshotTextResult] = field(default_factory=list)
    total_time_ms: float = 0.0

    @property
    def screenshot_count(self) -> int:
        """Total number of screenshots processed in the session."""
        return len(self.results)

    @property
    def is_empty(self) -> bool:
        """Return True if no text was extracted across any screenshot."""
        return all(r.line_count == 0 for r in self.results) or not self.results

    @property
    def total_lines(self) -> int:
        """Total line count across all screenshots."""
        return sum(r.line_count for r in self.results)

    @property
    def combined_text(self) -> str:
        """Combined structured text with clear, traceable screenshot boundaries."""
        if not self.results:
            return ""

        sections: list[str] = []
        for idx, res in enumerate(self.results, start=1):
            header = f"=== Screenshot {idx}: {res.screenshot_name} ==="
            content = res.combined_text.strip()
            if content:
                sections.append(f"{header}\n{content}")
            else:
                sections.append(f"{header}\n[No text recognized]")

        return "\n\n".join(sections)
