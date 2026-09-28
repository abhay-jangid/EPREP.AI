"""Application session management for in-memory screenshots."""

from dataclasses import dataclass, field
from pathlib import Path

from eprep.domain.exceptions import (
    DuplicateImageError,
    ImageValidationError,
    SessionCapacityError,
)
from eprep.domain.models import ScreenshotItem, ScreenshotSource
from eprep.infrastructure.imaging.processor import ImageLoader


@dataclass
class BatchAddResult:
    """Summary of batch screenshot addition (e.g. multi-select or drag-and-drop)."""

    added: list[ScreenshotItem] = field(default_factory=list)
    rejected_limit: list[str] = field(default_factory=list)
    rejected_unsupported: list[tuple[str, str]] = field(default_factory=list)
    rejected_duplicate: list[str] = field(default_factory=list)

    @property
    def status_message(self) -> str:
        """Generate a concise, user-friendly non-blocking status message."""
        messages: list[str] = []

        added_count = len(self.added)
        if added_count == 1:
            messages.append("1 screenshot added.")
        elif added_count > 1:
            messages.append(f"{added_count} screenshots added.")

        if self.rejected_limit:
            messages.append(f"Maximum of 5 reached ({len(self.rejected_limit)} ignored).")

        if self.rejected_duplicate:
            dup_count = len(self.rejected_duplicate)
            messages.append(
                "Screenshot already added." if dup_count == 1 else f"{dup_count} duplicate screenshots ignored."
            )

        if self.rejected_unsupported:
            unsup_count = len(self.rejected_unsupported)
            messages.append(
                f"{unsup_count} unsupported/unreadable file{'s' if unsup_count > 1 else ''} ignored."
            )

        if not messages:
            return "No valid screenshots found."

        return " ".join(messages)


class ScreenshotSession:
    """Manages an in-memory session of up to 5 problem screenshots."""

    MAX_SCREENSHOTS: int = 5

    def __init__(self) -> None:
        self._items: list[ScreenshotItem] = []

    @property
    def count(self) -> int:
        """Current count of active screenshots in session."""
        return len(self._items)

    @property
    def is_full(self) -> bool:
        """Return True if session has reached maximum capacity."""
        return self.count >= self.MAX_SCREENSHOTS

    @property
    def is_empty(self) -> bool:
        """Return True if session contains no screenshots."""
        return self.count == 0

    @property
    def items(self) -> list[ScreenshotItem]:
        """Return a shallow copy of active session items preserving insertion order."""
        return list(self._items)

    def has_duplicate_hash(self, content_hash: str) -> bool:
        """Check if an image with the identical content hash is already present."""
        return any(item.content_hash == content_hash for item in self._items)

    def add_item(self, item: ScreenshotItem) -> None:
        """Add a validated ScreenshotItem to the session.

        Raises:
            SessionCapacityError: If session is already full.
            DuplicateImageError: If an exact duplicate image is already present.
        """
        if self.is_full:
            raise SessionCapacityError(f"Maximum of {self.MAX_SCREENSHOTS} screenshots reached.")

        if self.has_duplicate_hash(item.content_hash):
            raise DuplicateImageError("Screenshot already added.")

        self._items.append(item)

    def add_from_path(self, file_path: Path | str) -> ScreenshotItem:
        """Load, validate, and add an image from a file path."""
        item = ImageLoader.load_from_path(file_path)
        self.add_item(item)
        return item

    def add_from_bytes(
        self,
        data: bytes,
        name: str = "Screenshot",
        source_type: str = ScreenshotSource.CLIPBOARD.value,
    ) -> ScreenshotItem:
        """Load, validate, and add an image from raw bytes."""
        if source_type == "paste":
            source_type = ScreenshotSource.CLIPBOARD.value
        item = ImageLoader.load_from_bytes(data, name=name, source_type=source_type)
        self.add_item(item)
        return item

    def add_multiple_paths(self, file_paths: list[Path | str]) -> BatchAddResult:
        """Process multiple file paths sequentially enforcing session limits and duplicate rules."""
        result = BatchAddResult()

        for raw_path in file_paths:
            path_str = str(raw_path)
            if self.is_full:
                result.rejected_limit.append(path_str)
                continue

            try:
                item = ImageLoader.load_from_path(raw_path)
                self.add_item(item)
                result.added.append(item)
            except DuplicateImageError:
                result.rejected_duplicate.append(path_str)
            except ImageValidationError as exc:
                result.rejected_unsupported.append((path_str, str(exc)))
            except SessionCapacityError:
                result.rejected_limit.append(path_str)

        return result

    def remove_item(self, item_id: str) -> bool:
        """Remove a screenshot by its unique ID. Returns True if removed, False if not found."""
        for idx, item in enumerate(self._items):
            if item.id == item_id:
                del self._items[idx]
                return True
        return False

    def clear(self) -> None:
        """Clear all active screenshots from session."""
        self._items.clear()
