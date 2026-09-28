"""Language selector widget for EPREP.AI."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from eprep.domain.language import SupportedLanguage


class LanguageSelector(QWidget):
    """Widget allowing the user to select the target programming language."""

    language_changed = Signal(SupportedLanguage)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._label = QLabel("Language:", self)
        self._label.setStyleSheet("font-weight: 500; color: #333;")

        self._combo = QComboBox(self)
        self._combo.setMinimumWidth(130)

        for lang in SupportedLanguage.get_all():
            self._combo.addItem(lang.value, lang)

        # Default to Python
        default_index = self._combo.findData(SupportedLanguage.PYTHON)
        if default_index >= 0:
            self._combo.setCurrentIndex(default_index)

        self._combo.currentIndexChanged.connect(self._on_index_changed)

        layout.addWidget(self._label)
        layout.addWidget(self._combo)

    def _on_index_changed(self, index: int) -> None:
        raw = self._combo.itemData(index)
        if raw is not None:
            self.language_changed.emit(SupportedLanguage(raw))

    def current_language(self) -> SupportedLanguage:
        """Return the currently selected language."""
        raw = self._combo.currentData()
        return SupportedLanguage(raw)

    def set_language(self, language: SupportedLanguage) -> None:
        """Set the current language selection."""
        index = self._combo.findText(language.value)
        if index >= 0:
            self._combo.setCurrentIndex(index)

    def available_languages(self) -> list[SupportedLanguage]:
        """Return all available languages in the selector."""
        return [SupportedLanguage(self._combo.itemText(i)) for i in range(self._combo.count())]
