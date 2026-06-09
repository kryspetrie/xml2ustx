"""Main window for the native xml2ustx desktop application."""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QDesktopServices, QDragEnterEvent, QDropEvent, QKeySequence
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLabel, QMainWindow, QMessageBox, QTabWidget, QVBoxLayout

from src.application.version import get_version
from src.ui.native.app_icon import load_app_icon
from src.ui.native.config_tab import ConfigTab
from src.ui.native.constants import mime_has_supported_paths, paths_from_mime
from src.ui.native.conversion_log import ConversionLog, ConversionLogWindow
from src.ui.native.conversion_presenter import ConversionPresenter
from src.ui.native.convert_tab import ConvertTab
from src.ui.native.openutau_path_dialog import OpenUtauPathDialog
from src.ui.native.theme import (
    THEME_DARK,
    THEME_LABELS,
    THEME_LIGHT,
    THEME_SYSTEM,
    apply_theme,
    bind_system_theme_updates,
    normalize_theme,
)
from src.ui.native.ui_settings import UiSettings
from src.ui.native.window_constraints import apply_main_window_constraints

PROJECT_GITHUB_URL = 'https://github.com/kryspetrie/xml2ustx'


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self, settings: UiSettings | None = None) -> None:
        super().__init__()
        self.setWindowTitle(f'xml2ustx {get_version()}')
        self.setWindowIcon(load_app_icon())
        apply_main_window_constraints(self)

        self._settings = settings or UiSettings()
        self._conversion_log = ConversionLog(self)
        self._log_window: ConversionLogWindow | None = None
        self._convert_tab_index = 0
        self._config_tab_index = 1
        self._last_tab_index = self._convert_tab_index
        self._block_tab_guard = False

        self._build_ui()
        self._build_menus()
        self._wire_presenter()
        self._restore_settings()
        self.setAcceptDrops(True)

    def _build_ui(self) -> None:
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self.config_tab = ConfigTab()
        self.convert_tab = ConvertTab(
            self.config_tab.config_file_path,
            self._settings,
            conversion_log=self._conversion_log,
        )
        self._tabs.addTab(self.convert_tab, self.tr('Convert'))
        self._tabs.addTab(self.config_tab, self.tr('Configuration'))

        self.config_tab.dirty_changed.connect(self._update_config_tab_title)
        self.config_tab.config_saved.connect(self._on_config_saved)
        self._tabs.currentChanged.connect(self._on_tab_changed)

        self._presenter = ConversionPresenter(self.convert_tab, self.config_tab, self._settings, self)
        self.convert_tab.convert_btn.clicked.connect(self._presenter.start_conversion)
        self.convert_tab.cancel_btn.clicked.connect(self._presenter.cancel_conversion)

        self.statusBar().showMessage(self.tr('Ready'))

    def _wire_presenter(self) -> None:
        self._presenter.log_line.connect(self.convert_tab.log_line)
        self._presenter.progress.connect(self.convert_tab.set_progress)
        self._presenter.validation_failed.connect(self._on_validation_failed)
        self._presenter.failed.connect(self._on_convert_failed)
        self._presenter.succeeded.connect(self._on_convert_ok)
        self._presenter.status_message.connect(self._on_status_message)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr('&File'))

        open_action = QAction(self.tr('&Open input…'), self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_input)
        file_menu.addAction(open_action)

        convert_action = QAction(self.tr('&Convert'), self)
        convert_action.setShortcut(QKeySequence('Ctrl+Return'))
        convert_action.triggered.connect(self._presenter.start_conversion)
        file_menu.addAction(convert_action)

        save_config_action = QAction(self.tr('&Save configuration'), self)
        save_config_action.setShortcut(QKeySequence.StandardKey.Save)
        save_config_action.triggered.connect(self._save_configuration)
        file_menu.addAction(save_config_action)

        config_action = QAction(self.tr('Edit &configuration…'), self)
        config_action.setShortcut('Ctrl+,')
        config_action.triggered.connect(self._show_config_tab)
        file_menu.addAction(config_action)

        openutau_action = QAction(self.tr('Set &OpenUtau path…'), self)
        openutau_action.triggered.connect(self._set_openutau_path)
        file_menu.addAction(openutau_action)

        file_menu.addSeparator()

        view_menu = self.menuBar().addMenu(self.tr('&View'))
        self._build_theme_menu(view_menu)

        log_action = QAction(self.tr('Conversion &log…'), self)
        log_action.triggered.connect(self._show_log_window)
        view_menu.addAction(log_action)

        file_menu.addSeparator()

        quit_action = QAction(self.tr('&Quit'), self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = self.menuBar().addMenu(self.tr('&Help'))
        about_action = QAction(self.tr('&About xml2ustx'), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        docs_action = QAction(self.tr('Project &documentation'), self)
        docs_action.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl(PROJECT_GITHUB_URL)),
        )
        help_menu.addAction(docs_action)

    def _open_input(self) -> None:
        self._tabs.setCurrentWidget(self.convert_tab)
        self.convert_tab.open_input_browser()

    def _show_config_tab(self) -> None:
        self._tabs.setCurrentIndex(self._config_tab_index)

    def _save_configuration(self) -> None:
        if self._tabs.currentWidget() != self.config_tab:
            self._show_config_tab()
        self.config_tab.save_config()

    def _build_theme_menu(self, view_menu) -> None:
        theme_menu = view_menu.addMenu(self.tr('&Theme'))
        self._theme_group = QActionGroup(self)
        self._theme_group.setExclusive(True)

        for theme_id in (THEME_SYSTEM, THEME_LIGHT, THEME_DARK):
            action = QAction(self.tr(THEME_LABELS[theme_id]), self)
            action.setCheckable(True)
            action.setData(theme_id)
            self._theme_group.addAction(action)
            theme_menu.addAction(action)
            if theme_id == self._settings.get_theme():
                action.setChecked(True)

        self._theme_group.triggered.connect(self._on_theme_selected)

    def _show_log_window(self) -> None:
        if self._log_window is None:
            self._log_window = ConversionLogWindow(self._conversion_log, self)
        self._log_window.show_and_raise()

    def _on_theme_selected(self, action: QAction) -> None:
        theme = normalize_theme(str(action.data() or ''))
        if theme == self._settings.get_theme():
            return

        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, theme)

        self._settings.set_theme(theme)
        self._settings.sync()
        self.statusBar().showMessage(
            self.tr('Theme set to {theme}').format(theme=self.tr(THEME_LABELS[theme])),
            5000,
        )

    def _set_openutau_path(self) -> None:
        dialog = OpenUtauPathDialog(self._settings, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        path = self._settings.get_openutau_path().strip()
        if path:
            self.statusBar().showMessage(
                self.tr('OpenUtau path set to {path}').format(path=path),
                5000,
            )
        else:
            self.statusBar().showMessage(self.tr('OpenUtau path cleared'), 5000)

    def _on_tab_changed(self, index: int) -> None:
        if self._block_tab_guard:
            return

        previous = self._last_tab_index
        if (
            previous == self._config_tab_index
            and index != self._config_tab_index
            and self.config_tab.is_dirty()
            and not self.config_tab.ensure_saved()
        ):
            self._block_tab_guard = True
            self._tabs.setCurrentIndex(previous)
            self._block_tab_guard = False
            return

        self._last_tab_index = index
        self._settings.set_int('last_tab_index', index)

    def _on_config_saved(self, _path: str) -> None:
        self.convert_tab.reload_config_metadata()

    def _update_config_tab_title(self, dirty: bool) -> None:
        title = self.tr('Configuration')
        self._tabs.setTabText(self._config_tab_index, f'{title} *' if dirty else title)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if mime_has_supported_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = paths_from_mime(event.mimeData())
        if paths:
            self._tabs.setCurrentWidget(self.convert_tab)
            self.convert_tab.ingest_dropped_paths(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_validation_failed(self, message: str) -> None:
        QMessageBox.warning(self, self.tr('Cannot convert'), message)

    def _on_convert_ok(self, outputs: list) -> None:
        self.convert_tab.log_line(self.tr('Conversion finished.'))
        self.statusBar().showMessage(self.tr('Conversion finished'), 5000)
        QMessageBox.information(
            self,
            self.tr('Done'),
            self.tr('Created {count} USTX file(s).').format(count=len(outputs)),
        )

    def _on_convert_failed(self, message: str) -> None:
        self.convert_tab.log_line(f'{self.tr("Error")}: {message}')
        self.statusBar().showMessage(self.tr('Conversion failed'), 5000)
        QMessageBox.critical(self, self.tr('Conversion failed'), message)

    def _on_status_message(self, message: str, timeout_ms: int) -> None:
        if timeout_ms > 0:
            self.statusBar().showMessage(message, timeout_ms)
        else:
            self.statusBar().showMessage(message)

    def _show_about(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr('About xml2ustx'))
        layout = QVBoxLayout(dialog)

        label = QLabel(
            self.tr(
                '<h3>xml2ustx {version}</h3>'
                '<p>Convert MusicXML vocal parts to OpenUtau USTX projects.</p>'
                '<p>CLI: <code>xml2ustx-cli</code> &nbsp; GUI: <code>xml2ustx</code></p>'
                '<p><a href="{url}">Project on GitHub</a></p>',
            ).format(version=get_version(), url=PROJECT_GITHUB_URL),
        )
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setOpenExternalLinks(True)
        label.setWordWrap(True)
        layout.addWidget(label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

    def _restore_settings(self) -> None:
        self._settings.restore_window(self)
        config = self._settings.get_str('config_path')
        if config:
            self.config_tab.set_config_path(config)
        self.convert_tab.apply_settings(self._settings)

        last_tab = self._settings.get_int('last_tab_index', self._convert_tab_index)
        if last_tab in {self._convert_tab_index, self._config_tab_index}:
            self._block_tab_guard = True
            self._tabs.setCurrentIndex(last_tab)
            self._last_tab_index = last_tab
            self._block_tab_guard = False

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._presenter.is_busy():
            reply = QMessageBox.question(
                self,
                self.tr('Conversion in progress'),
                self.tr('A conversion is still running. Cancel and quit?'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._presenter.shutdown()

        if not self.config_tab.confirm_discard_on_close():
            event.ignore()
            return

        self._settings.save_window(self)
        self._settings.set_str('config_path', self.config_tab.config_file_path())
        self.convert_tab.save_settings(self._settings)
        self._settings.sync()
        super().closeEvent(event)


def run_app() -> int:
    """Launch the native Qt UI."""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough,
    )
    app = QApplication(sys.argv)
    app.setApplicationName('xml2ustx')
    app.setOrganizationName('xml2ustx')
    app.setDesktopFileName('xml2ustx')
    app.setWindowIcon(load_app_icon())
    settings = UiSettings()
    apply_theme(app, settings.get_theme())
    bind_system_theme_updates(app)
    window = MainWindow(settings)
    window.show()
    return app.exec()
