"""Dialog for configuring the OpenUtau executable path in the native UI."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QUrl
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.application.openutau_launcher import MACOS_DEFAULT_APP, is_valid_openutau_path
from src.ui.native.ui_settings import UiSettings


def mac_applications_dir() -> str:
    """Return the system Applications directory on macOS."""
    locations = QStandardPaths.standardLocations(
        QStandardPaths.StandardLocation.ApplicationsLocation,
    )
    for location in locations:
        if location and Path(location).is_dir():
            return location
    return '/Applications'


class OpenUtauPathDialog(QDialog):
    """Prompt for the OpenUtau binary used by the GUI."""

    def __init__(self, settings: UiSettings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle(self.tr('OpenUtau path'))
        self._build_ui()
        self._load_current_path()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        if sys.platform == 'darwin':
            hint = self.tr(
                'Browse opens the Applications folder directly — select OpenUtau.app, not the '
                'Applications folder itself. You can also paste /Applications/OpenUtau.app '
                'or use the default button below.',
            )
        else:
            hint = self.tr(
                'Choose the OpenUtau application binary. '
                'This path is saved in xml2ustx settings and is not read from environment variables.',
            )
        layout.addWidget(QLabel(hint))

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setAccessibleName(self.tr('OpenUtau binary path'))
        browse_label = self.tr('Browse Applications…') if sys.platform == 'darwin' else self.tr('Browse…')
        browse_btn = QPushButton(browse_label)
        browse_btn.clicked.connect(self._browse)
        clear_btn = QPushButton(self.tr('Clear'))
        clear_btn.clicked.connect(self.path_edit.clear)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse_btn)
        path_row.addWidget(clear_btn)
        layout.addLayout(path_row)

        if sys.platform == 'darwin':
            default_row = QHBoxLayout()
            default_btn = QPushButton(self.tr('Use /Applications/OpenUtau.app'))
            default_btn.clicked.connect(self._use_default_mac_app)
            default_row.addWidget(default_btn)
            default_row.addStretch()
            layout.addLayout(default_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_current_path(self) -> None:
        self.path_edit.setText(self._settings.get_openutau_path())

    def _browse_start_dir(self) -> str:
        if sys.platform == 'darwin':
            current = self.path_edit.text().strip()
            if current:
                current_path = Path(current).expanduser()
                if current_path.suffix == '.app' and current_path.parent.is_dir():
                    return str(current_path.parent)
            applications_dir = Path(mac_applications_dir())
            if applications_dir.is_dir():
                return str(applications_dir)

        current = self.path_edit.text().strip()
        if current:
            current_path = Path(current).expanduser()
            if current_path.is_dir():
                return str(current_path)
            if current_path.exists():
                return str(current_path.parent)
            if current_path.parent.exists():
                return str(current_path.parent)

        return str(Path.home())

    def _browse_mac_application(self) -> str:
        applications_dir = mac_applications_dir()
        dialog = QFileDialog(self, self.tr('OpenUtau application'))
        dialog.setDirectory(applications_dir)
        dialog.setNameFilter(self.tr('Applications (*.app);;All files (*)'))
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setSidebarUrls([
            QUrl.fromLocalFile(applications_dir),
            QUrl.fromLocalFile(str(Path.home())),
        ])
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return ''
        selected = dialog.selectedFiles()
        return selected[0] if selected else ''

    def _browse(self) -> None:
        if sys.platform == 'darwin':
            path = self._browse_mac_application()
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                self.tr('OpenUtau executable'),
                self._browse_start_dir(),
                self.tr('All files (*)'),
            )
        if path:
            self.path_edit.setText(path)

    def _use_default_mac_app(self) -> None:
        if MACOS_DEFAULT_APP.exists():
            self.path_edit.setText(str(MACOS_DEFAULT_APP))
            return

        QMessageBox.information(
            self,
            self.tr('OpenUtau path'),
            self.tr('OpenUtau.app was not found in /Applications.'),
        )

    def _save(self) -> None:
        path = self.path_edit.text().strip()
        if path and not is_valid_openutau_path(path):
            if sys.platform == 'darwin' and path.endswith('.app'):
                message = self.tr(
                    'The selected application bundle does not look like a valid OpenUtau install.',
                )
            else:
                message = self.tr('The selected path does not exist or is not a launchable OpenUtau binary.')
            QMessageBox.warning(self, self.tr('OpenUtau path'), message)
            return

        self._settings.set_openutau_path(path)
        self._settings.sync()
        self.accept()
