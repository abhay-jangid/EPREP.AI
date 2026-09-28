"""Supported programming language definitions for EPREP.AI."""

from enum import Enum


class SupportedLanguage(str, Enum):
    """Initial programming languages supported by EPREP.AI V1.

    Strict invariant: Exactly 6 languages are supported in V1.
    """

    PYTHON = "Python"
    JAVA = "Java"
    C = "C"
    CPP = "C++"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"

    @classmethod
    def get_all(cls) -> list["SupportedLanguage"]:
        """Return all supported languages."""
        return list(cls)

    @classmethod
    def get_names(cls) -> list[str]:
        """Return string display names for all supported languages."""
        return [lang.value for lang in cls]
