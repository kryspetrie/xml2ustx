"""Application-wide Qt styling for the native UI."""
from __future__ import annotations

from PySide6.QtWidgets import QApplication

_HELP_TEXT_COLORS = {
    'light': '#424242',
    'dark': '#CCCCCC',
}


def application_stylesheet(resolved_scheme: str = 'light') -> str:
    """Return a subtle stylesheet shared by the native desktop app."""
    scheme = resolved_scheme if resolved_scheme in _HELP_TEXT_COLORS else 'light'
    help_color = _HELP_TEXT_COLORS[scheme]
    return f"""
    QMainWindow {{
        font-size: 13px;
    }}
    QGroupBox {{
        font-weight: 600;
        margin-top: 12px;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
    }}
    QLabel#formHelpText {{
        color: {help_color};
        font-size: 12px;
        padding-top: 4px;
    }}
    QPlainTextEdit#configEditor, QPlainTextEdit#conversionLog {{
        font-family: "Monospace", "Courier New", monospace;
    }}
    QTableView#paddedTableView::item {{
        padding-left: 8px;
        padding-right: 8px;
    }}
    QProgressBar {{
        min-height: 18px;
        text-align: center;
    }}
    QPushButton:default {{
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        font-weight: 600;
    }}
    QPushButton, QLabel, QLineEdit, QPlainTextEdit, QTableView, QListWidget,
    QSpinBox, QCheckBox, QComboBox, QTabWidget, QScrollArea {{
        font-size: 13px;
    }}
    QLineEdit, QComboBox, QPushButton, QSpinBox {{
        min-height: 28px;
    }}
    """


def apply_application_style(app: QApplication) -> None:
    """Apply shared styling to the running application."""
    scheme = str(app.property('xml2ustx_resolved_scheme') or 'light')
    app.setStyleSheet(application_stylesheet(scheme))
