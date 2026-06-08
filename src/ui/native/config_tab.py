"""Configuration editor tab for the native UI."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.native.config_data import parse_config_document
from src.ui.native.config_form_editor import ConfigFormEditor
from src.ui.native.config_store import (
    default_config_path,
    read_config_text,
    shipped_config_text,
    validate_config_yaml,
    write_config_text,
)
from src.ui.native.constants import CONFIG_FILTER


class ConfigTab(QWidget):
    """Configuration editor with visual and YAML source modes."""

    dirty_changed = Signal(bool)
    config_saved = Signal(str)

    _FORM_TAB = 0
    _SOURCE_TAB = 1

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._dirty = False
        self._block_tab_sync = False
        self._build_ui()
        self._reload_editor()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        path_row = QHBoxLayout()
        self.config_path = QLineEdit()
        self.config_path.setText(default_config_path())
        self.config_path.setAccessibleName(self.tr('Config file path'))
        browse_cfg = QPushButton(self.tr('Browse…'))
        browse_cfg.clicked.connect(self._browse_config)
        path_row.addWidget(QLabel(self.tr('Config file')))
        path_row.addWidget(self.config_path, 1)
        path_row.addWidget(browse_cfg)
        layout.addLayout(path_row)
        path_label = path_row.itemAt(0).widget()
        if isinstance(path_label, QLabel):
            path_label.setBuddy(self.config_path)

        self.editor_tabs = QTabWidget()
        self.form_editor = ConfigFormEditor()
        self.form_editor.changed.connect(self._mark_dirty)
        self.editor_tabs.addTab(self.form_editor, self.tr('Visual editor'))

        self.config_editor = QPlainTextEdit()
        self.config_editor.setObjectName('configEditor')
        font = self.config_editor.font()
        font.setStyleHint(font.StyleHint.Monospace)
        self.config_editor.setFont(font)
        self.config_editor.setAccessibleName(self.tr('Config editor'))
        self.config_editor.textChanged.connect(self._mark_dirty)
        self.editor_tabs.addTab(self.config_editor, self.tr('Edit file'))

        self.editor_tabs.currentChanged.connect(self._on_editor_tab_changed)
        layout.addWidget(self.editor_tabs, 1)

        btn_row = QHBoxLayout()
        reload_btn = QPushButton(self.tr('Reload'))
        reload_btn.clicked.connect(self._reload_editor)
        save_btn = QPushButton(self.tr('Save'))
        save_btn.clicked.connect(self.save_config)
        reset_btn = QPushButton(self.tr('Reset to default'))
        reset_btn.clicked.connect(self._reset_config)
        import_btn = QPushButton(self.tr('Import…'))
        import_btn.clicked.connect(self._import_config)
        btn_row.addWidget(reload_btn)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(reset_btn)
        btn_row.addWidget(import_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def config_file_path(self) -> str:
        """Return the active config file path."""
        return self.config_path.text().strip() or default_config_path()

    def is_dirty(self) -> bool:
        """Return ``True`` when the editor has unsaved changes."""
        return self._dirty

    def ensure_saved(self) -> bool:
        """Prompt to save dirty changes. Returns ``False`` if the user cancelled."""
        if not self._dirty:
            return True

        reply = QMessageBox.question(
            self,
            self.tr('Unsaved configuration'),
            self.tr('Save changes to the config file before continuing?'),
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return False
        if reply == QMessageBox.StandardButton.Save:
            return self.save_config()
        self._set_dirty(False)
        return True

    def save_config(self) -> bool:
        """Validate and write the editor buffer to disk."""
        path = self.config_file_path()
        try:
            text = self._editor_text()
            validate_config_yaml(text)
            write_config_text(path, text)
            self._set_editor_text(text)
            self._set_dirty(False)
            self.config_saved.emit(path)
            return True
        except Exception as exc:
            QMessageBox.critical(self, self.tr('Invalid config'), str(exc))
            return False

    def set_config_path(self, path: str) -> None:
        """Set the config path field and reload when it changed."""
        if self.config_path.text().strip() != path:
            self.config_path.setText(path)
            self._reload_editor()

    def _mark_dirty(self) -> None:
        self._set_dirty(True)

    def _set_dirty(self, dirty: bool) -> None:
        if self._dirty != dirty:
            self._dirty = dirty
            self.dirty_changed.emit(dirty)

    def _editor_text(self) -> str:
        if self.editor_tabs.currentIndex() == self._FORM_TAB:
            return self.form_editor.to_text()
        return self.config_editor.toPlainText()

    def _set_editor_text(self, text: str) -> None:
        self.config_editor.blockSignals(True)
        self.form_editor.blockSignals(True)
        try:
            self.config_editor.setPlainText(text)
            self.form_editor.load_text(text)
        finally:
            self.config_editor.blockSignals(False)
            self.form_editor.blockSignals(False)

    def _sync_to_source(self) -> None:
        text = self.form_editor.to_text()
        self.config_editor.blockSignals(True)
        try:
            self.config_editor.setPlainText(text)
        finally:
            self.config_editor.blockSignals(False)

    def _sync_to_form(self) -> bool:
        text = self.config_editor.toPlainText()
        try:
            parse_config_document(text)
            self.form_editor.load_text(text)
            return True
        except Exception as exc:
            QMessageBox.critical(
                self,
                self.tr('Invalid config'),
                self.tr('Could not load the visual editor:\n{error}').format(error=exc),
            )
            return False

    def _on_editor_tab_changed(self, index: int) -> None:
        if self._block_tab_sync:
            return

        previous = self._SOURCE_TAB if index == self._FORM_TAB else self._FORM_TAB
        self._block_tab_sync = True
        try:
            if previous == self._FORM_TAB and index == self._SOURCE_TAB:
                self._sync_to_source()
            elif previous == self._SOURCE_TAB and index == self._FORM_TAB:
                if not self._sync_to_form():
                    self.editor_tabs.setCurrentIndex(self._SOURCE_TAB)
        finally:
            self._block_tab_sync = False

    def _browse_config(self) -> None:
        if not self.ensure_saved():
            return
        path, _ = QFileDialog.getOpenFileName(self, self.tr('Config file'), filter=CONFIG_FILTER)
        if path:
            self.config_path.setText(path)
            self._reload_editor()

    def _import_config(self) -> None:
        if not self.ensure_saved():
            return
        path, _ = QFileDialog.getOpenFileName(self, self.tr('Import config'), filter=CONFIG_FILTER)
        if path:
            self.config_path.setText(path)
            self._reload_editor()

    def _reload_editor(self) -> None:
        if self._dirty:
            reply = QMessageBox.question(
                self,
                self.tr('Discard changes?'),
                self.tr('Reload the config file and discard unsaved edits?'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        path = self.config_file_path()
        try:
            self._set_editor_text(read_config_text(path))
            self._set_dirty(False)
        except OSError as exc:
            QMessageBox.warning(self, self.tr('Config'), str(exc))

    def _reset_config(self) -> None:
        reply = QMessageBox.question(
            self,
            self.tr('Reset configuration'),
            self.tr('Replace the editor contents with the shipped default config?'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._set_editor_text(shipped_config_text())
            self._mark_dirty()

    def confirm_discard_on_close(self) -> bool:
        """Return ``False`` when the user cancels closing with unsaved edits."""
        return self.ensure_saved()
