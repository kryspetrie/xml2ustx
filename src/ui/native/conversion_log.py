"""Conversion log session and viewer window."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ConversionLog(QObject):
    """In-memory conversion log shared by the convert tab and log viewer."""

    line_appended = Signal(str)
    cleared = Signal()

    _MAX_LINES = 500

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._lines: list[str] = []

    def append(self, message: str) -> None:
        """Append a timestamped line to the session log."""
        stamp = datetime.now().strftime('%H:%M:%S')
        line = f'[{stamp}] {message}'
        self._lines.append(line)
        if len(self._lines) > self._MAX_LINES:
            self._lines = self._lines[-self._MAX_LINES:]
        self.line_appended.emit(line)

    def text(self) -> str:
        return '\n'.join(self._lines)

    def clear(self) -> None:
        self._lines.clear()
        self.cleared.emit()


class ConversionLogWindow(QMainWindow):
    """Secondary window for viewing conversion log output."""

    def __init__(self, log: ConversionLog, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._log = log
        self.setWindowTitle(self.tr('Conversion log'))
        self.setMinimumSize(520, 360)
        self.resize(640, 420)

        central = QWidget()
        layout = QVBoxLayout(central)

        self._editor = QPlainTextEdit()
        self._editor.setObjectName('conversionLog')
        self._editor.setReadOnly(True)
        self._editor.setPlainText(log.text())
        self._editor.setAccessibleName(self.tr('Conversion log'))
        layout.addWidget(self._editor, 1)

        btn_row = QHBoxLayout()
        copy_btn = QPushButton(self.tr('Copy log'))
        copy_btn.clicked.connect(self._copy_log)
        save_btn = QPushButton(self.tr('Save log…'))
        save_btn.clicked.connect(self._save_log)
        clear_btn = QPushButton(self.tr('Clear log'))
        clear_btn.clicked.connect(self._clear_log)
        btn_row.addWidget(copy_btn)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.setCentralWidget(central)

        log.line_appended.connect(self._append_line)
        log.cleared.connect(self._editor.clear)

    def show_and_raise(self) -> None:
        """Show the log window and bring it to the front."""
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()

    def _append_line(self, line: str) -> None:
        self._editor.appendPlainText(line)

    def _copy_log(self) -> None:
        QGuiApplication.clipboard().setText(self._editor.toPlainText())

    def _save_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr('Save conversion log'),
            '',
            self.tr('Log files (*.log);;Text files (*.txt);;All files (*)'),
        )
        if not path:
            return
        Path(path).write_text(self._editor.toPlainText(), encoding='utf-8')
        self._log.append(self.tr('Log saved to {path}').format(path=path))

    def _clear_log(self) -> None:
        self._log.clear()
