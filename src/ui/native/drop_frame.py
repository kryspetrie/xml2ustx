"""Visual drop target for MusicXML and MIDI files."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from src.ui.native.constants import paths_from_mime, mime_has_supported_paths


class DropFrame(QFrame):
    """Styled frame that accepts supported local file/folder drops."""

    def __init__(self, on_drop: Callable[[list[str]], None], parent=None):
        super().__init__(parent)
        self._on_drop = on_drop
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setMinimumHeight(72)

        layout = QVBoxLayout(self)
        self.label = QLabel(self.tr('Drop MusicXML / MIDI files or folders here'))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setAccessibleName(self.tr('Drop target'))
        layout.addWidget(self.label)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if mime_has_supported_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = paths_from_mime(event.mimeData())
        if paths:
            self._on_drop(paths)
            event.acceptProposedAction()
        else:
            event.ignore()
