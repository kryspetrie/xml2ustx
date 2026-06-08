"""Application icon helpers for the native UI."""
from __future__ import annotations

from PySide6.QtGui import QIcon

from src.resources.Resources import get_resource_path


def load_app_icon() -> QIcon:
    """Return the xml2ustx application icon from packaged resources."""
    return QIcon(str(get_resource_path('logo.png')))
