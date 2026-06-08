"""Conversion workflow presenter (coordinates view, config, and worker thread)."""
from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from src.application.JobBuilder import get_input_files_from_dir
from src.application.models.NativeUiOptions import NativeUiOptions
from src.ui.native.config_tab import ConfigTab
from src.ui.native.convert_options import build_native_ui_options
from src.ui.native.convert_tab import ConvertTab
from src.ui.native.ui_settings import UiSettings
from src.ui.native.worker import ConvertWorker


class ConversionPresenter(QObject):
    """Orchestrates conversion jobs without owning widgets directly."""

    log_line = Signal(str)
    progress = Signal(int, int)
    succeeded = Signal(list)
    failed = Signal(str)
    validation_failed = Signal(str)
    busy_changed = Signal(bool)
    status_message = Signal(str, int)

    def __init__(
            self,
            convert_tab: ConvertTab,
            config_tab: ConfigTab,
            settings: UiSettings,
            parent: QObject | None = None):
        super().__init__(parent)
        self._convert_tab = convert_tab
        self._config_tab = config_tab
        self._settings = settings
        self._thread: QThread | None = None
        self._worker: ConvertWorker | None = None

    def is_busy(self) -> bool:
        """Return ``True`` while a conversion thread is running."""
        return self._thread is not None and self._thread.isRunning()

    def start_conversion(self) -> None:
        """Validate inputs and start a background conversion."""
        if self.is_busy():
            return

        if not self._config_tab.ensure_saved():
            return

        try:
            state = self._convert_tab.form_state()
            config_file = self._config_tab.config_file_path()
            openutau_path = self._settings.get_openutau_path().strip() or None
            options = build_native_ui_options(
                state,
                config_file,
                openutau_path=openutau_path,
            )
        except ValueError as exc:
            self.validation_failed.emit(str(exc))
            return

        file_count = _file_count(options)
        self._convert_tab.set_busy(True)
        self._convert_tab.reset_progress()
        self._convert_tab.set_progress(0, max(file_count, 1), self.tr('Starting…'))
        self.busy_changed.emit(True)
        self.status_message.emit(self.tr('Converting…'), 0)

        self._thread = QThread()
        self._worker = ConvertWorker(options)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.log_line.connect(self.log_line.emit)
        self._worker.progress.connect(self.progress.emit)
        self._worker.succeeded.connect(self._on_succeeded)
        self._worker.failed.connect(self.failed.emit)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._clear_worker_refs)

        self._thread.start()
        self._settings.set_str('track_preset', self._convert_tab.track_preset.currentText())
        self._persist_convert_preferences(state)

    def cancel_conversion(self) -> None:
        """Request cooperative cancellation."""
        if self._worker is not None:
            self._worker.request_cancel()
            self.status_message.emit(self.tr('Cancelling…'), 0)

    def shutdown(self) -> None:
        """Stop an in-flight conversion during application exit."""
        if self._thread is not None and self._thread.isRunning():
            if self._worker is not None:
                self._worker.request_cancel()
            self._thread.quit()
            self._thread.wait(3000)

    def _on_succeeded(self, outputs: list) -> None:
        self._convert_tab.remember_last_output(outputs)
        self.succeeded.emit(outputs)

    def _on_finished(self) -> None:
        self._convert_tab.set_busy(False)
        self._convert_tab.reset_progress()
        self.busy_changed.emit(False)

    def _clear_worker_refs(self) -> None:
        self._thread = None
        self._worker = None

    def _persist_convert_preferences(self, state) -> None:
        self._settings.set_bool('debug', state.debug)
        self._settings.set_bool('open_in_openutau', state.open_in_openutau)
        self._settings.set_bool('batch_mode', state.batch_mode)
        if state.input_path:
            self._settings.set_str('last_input_path', state.input_path)
        self._settings.set_str('project_name', state.project_name)
        self._settings.set_bool('use_custom_tracks', state.use_custom_tracks)


def _file_count(options: NativeUiOptions) -> int:
    if options.input_dir:
        return len(get_input_files_from_dir(options.input_dir))
    return len(options.input_files)
