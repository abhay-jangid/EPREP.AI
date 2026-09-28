"""Domain models for EPREP.AI."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenshotItem:
    """Represents a single in-memory screenshot item within a problem session."""

    id: str
    name: str
    source_type: str
    width: int
    height: int
    format: str
    content_hash: str
    image_bytes: bytes

    @property
    def dimensions(self) -> tuple[int, int]:
        """Return dimensions as (width, height)."""
        return self.width, self.height
