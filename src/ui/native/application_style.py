"""Application-wide Qt styling for the native UI."""
from __future__ import annotations

from PySide6.QtWidgets import QApplication


def application_stylesheet() -> str:
    """Return a subtle stylesheet shared by the native desktop app."""
    return """
    QMainWindow, QWidget {
        font-size: 13px;
    }
    QGroupBox {
        font-weight: 600;
        margin-top: 10px;
        padding-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
    }
    QPlainTextEdit#configEditor, QPlainTextEdit#conversionLog {
        font-family: "Monospace", "Courier New", monospace;
    }
    QProgressBar {
        min-height: 18px;
        text-align: center;
    }
    QPushButton:default {
        font-weight: 600;
    }
    QTabBar::tab:selected {
        font-weight: 600;
    }
    """


def apply_application_style(app: QApplication) -> None:
    """Apply shared styling to the running application."""
    app.setStyleSheet(application_stylesheet())
