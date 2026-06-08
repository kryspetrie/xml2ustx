"""Background conversion worker using Qt's recommended threading pattern."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from src.application.conversion_errors import ConversionCancelledError, ConversionError
from src.application.models.NativeUiOptions import NativeUiOptions
from src.application.openutau_launcher import open_in_openutau
from src.application.Xml2UstxRunner import run_native


class ConvertWorker(QObject):
    """Runs MusicXML → USTX conversion off the UI thread."""

    log_line = Signal(str)
    succeeded = Signal(list)
    failed = Signal(str)
    progress = Signal(int, int)
    finished = Signal()

    def __init__(self, options: NativeUiOptions):
        super().__init__()
        self._options = options
        self._cancelled = False

    @Slot()
    def run(self) -> None:
        """Execute the conversion job (invoked on the worker thread)."""
        try:
            if self._cancelled:
                return

            def log_fn(message: str) -> None:
                self.log_line.emit(message)

            def progress_fn(current: int, total: int) -> None:
                self.progress.emit(current, total)

            outputs = run_native(
                self._options,
                log_fn=log_fn,
                should_cancel=lambda: self._cancelled,
                progress_fn=progress_fn,
            )
            if self._cancelled:
                self.log_line.emit(self.tr('Conversion cancelled.'))
                return

            if self._options.open_in_openutau:
                opened = open_in_openutau(
                    outputs,
                    openutau_path=self._options.openutau_path,
                    allow_env_fallback=False,
                    log_fn=log_fn,
                )
                if not opened:
                    self.log_line.emit(self.tr('Warning: could not open OpenUtau (see log above).'))

            self.succeeded.emit(outputs)
        except ConversionCancelledError:
            self.log_line.emit(self.tr('Conversion cancelled.'))
        except ConversionError as exc:
            self.failed.emit(exc.formatted())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()

    def request_cancel(self) -> None:
        """Request cooperative cancellation before the next input file."""
        self._cancelled = True
