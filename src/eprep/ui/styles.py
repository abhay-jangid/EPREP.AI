"""Centralized desktop UI styling and dark theme definitions for EPREP.AI."""

DARK_THEME_STYLESHEET = """
QMainWindow {
    background-color: #0f172a;
}

QWidget {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #f8fafc;
}

QLabel {
    color: #e2e8f0;
    background: transparent;
}

QComboBox {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #475569;
}

QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    outline: none;
    padding: 4px;
}

QPushButton {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton:hover:!disabled {
    background-color: #273549;
    border-color: #475569;
}

QPushButton:disabled {
    background-color: #141c2b;
    color: #64748b;
    border-color: #1e293b;
}

QTabWidget::pane {
    border: 1px solid #334155;
    background-color: #0f172a;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 7px 16px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 3px;
    font-size: 12px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
    border-bottom: 1px solid #0f172a;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #273549;
    color: #cbd5e1;
}

QPlainTextEdit {
    background-color: #090d16;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 10px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QSplitter::handle {
    background-color: #1e293b;
    width: 2px;
}

QStatusBar {
    background-color: #090d16;
    color: #94a3b8;
    border-top: 1px solid #1e293b;
    font-size: 12px;
    padding: 2px 6px;
}

QToolTip {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
"""
