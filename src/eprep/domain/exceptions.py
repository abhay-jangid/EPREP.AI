"""Domain exception hierarchy for EPREP.AI."""


class EprepError(Exception):
    """Base exception for all EPREP.AI domain and application errors."""


class ScreenshotError(EprepError):
    """Base exception for screenshot-related errors."""


class ImageValidationError(ScreenshotError):
    """Raised when an image fails format, dimension, or integrity validation."""


class SessionCapacityError(ScreenshotError):
    """Raised when an operation would exceed the session screenshot limit."""


class DuplicateImageError(ScreenshotError):
    """Raised when attempting to add an exact duplicate image to an active session."""
