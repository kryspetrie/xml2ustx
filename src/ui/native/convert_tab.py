"""Convert tab for the native xml2ustx desktop application."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.application.ListTrackConfigs import list_groove_preset_ids, list_swing_preset_ids, list_track_config_ids
from src.application.ConfigParser import parse as parse_config
from src.application.JobBuilder import get_input_files_from_dir, to_output_file
from src.application.models.NativeUiOptions import NativeUiOptions
from src.ui.native.constants import INPUT_FILTER, USTX_FILTER, is_supported_input
from src.ui.native.conversion_log import ConversionLog
from src.ui.native.convert_options import build_native_ui_options
from src.ui.native.drop_frame import DropFrame
from src.ui.native.models.convert_form_state import ConvertFormState
from src.ui.native.table_columns import configure_track_table_columns
from src.ui.native.track_delegates import DoubleSpinDelegate, VoiceIdDelegate
from src.ui.native.track_table_model import TrackTableModel
from src.ui.native.ui_settings import UiSettings

NONE_PRESET_LABEL = '(None)'
NONE_PRESET_ID = ''

_FORM_MARGINS = (12, 12, 12, 12)
_FORM_H_SPACING = 16
_FORM_V_SPACING = 10
_SECTION_SPACING = 10
_PAGE_MARGINS = (16, 16, 16, 16)


class ConvertTab(QWidget):
    """MusicXML/MIDI conversion controls."""

    def __init__(
            self,
            config_path_provider: Callable[[], str],
            settings: UiSettings | None = None,
            *,
            conversion_log: ConversionLog | None = None,
            parent: QWidget | None = None):
        super().__init__(parent)
        self._config_path_provider = config_path_provider
        self._settings = settings or UiSettings()
        self._conversion_log = conversion_log or ConversionLog(self)
        self._voice_ids: list[str] = []
        self._last_output_dir: str | None = None
        self.track_model = TrackTableModel(parent=self)
        self._build_ui()
        self.reload_config_metadata()

    @property
    def conversion_log(self) -> ConversionLog:
        return self._conversion_log

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*_PAGE_MARGINS)
        layout.setSpacing(_SECTION_SPACING)

        self.drop_frame = DropFrame(self.ingest_dropped_paths, self)
        layout.addWidget(self.drop_frame)

        input_group = QGroupBox(self.tr('Input & output'))
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(*_FORM_MARGINS)
        input_layout.setSpacing(_FORM_V_SPACING)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(12)
        self.mode_single = QRadioButton(self.tr('Single / multiple files'))
        self.mode_single.setChecked(True)
        self.mode_dir = QRadioButton(self.tr('Input directory (batch)'))
        self.mode_single.toggled.connect(self._update_mode_ui)
        mode_row.addWidget(self.mode_single)
        mode_row.addWidget(self.mode_dir)
        mode_row.addStretch()
        input_layout.addLayout(mode_row)

        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText(self.tr('Input file or folder…'))
        self.input_path.setAccessibleName(self.tr('Input path'))
        browse_in = QPushButton(self.tr('Browse…'))
        browse_in.clicked.connect(self._browse_input)
        file_row.addWidget(self.input_path, 1)
        file_row.addWidget(browse_in)
        input_layout.addLayout(file_row)

        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(100)
        self.file_list.setAccessibleName(self.tr('Input file list'))
        self.file_list.itemSelectionChanged.connect(self._update_output_mode)
        input_layout.addWidget(self.file_list)

        self.auto_output = QCheckBox(self.tr('Auto output path (.ustx next to input)'))
        self.auto_output.setChecked(True)
        self.auto_output.toggled.connect(self._update_output_mode)
        input_layout.addWidget(self.auto_output)

        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self.output_path = QLineEdit()
        self.output_path.setEnabled(False)
        self.output_path.setAccessibleName(self.tr('Output path'))
        browse_out = QPushButton(self.tr('Browse…'))
        browse_out.clicked.connect(self._browse_output)
        out_row.addWidget(self.output_path, 1)
        out_row.addWidget(browse_out)
        input_layout.addLayout(out_row)
        layout.addWidget(input_group)
        self.input_group = input_group

        columns = QHBoxLayout()
        columns.setSpacing(20)

        self._options_left = QWidget()
        left_column = QVBoxLayout(self._options_left)
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(_SECTION_SPACING)

        self._options_right = QWidget()
        right_column = QVBoxLayout(self._options_right)
        right_column.setContentsMargins(0, 0, 0, 0)
        right_column.setSpacing(_SECTION_SPACING)

        self.project_group = QGroupBox(self.tr('Project'))
        project_form = QFormLayout(self.project_group)
        self._configure_form_layout(project_form)
        self.project_name = QLineEdit(self.tr('New Project'))
        self.project_name.setAccessibleName(self.tr('Project name'))
        self._expand_form_field(self.project_name)
        project_form.addRow(self.tr('Project name'), self.project_name)

        self.track_preset = QComboBox()
        self.track_preset.setAccessibleName(self.tr('Track preset'))
        self._expand_form_field(self.track_preset)
        project_form.addRow(self.tr('Track preset'), self.track_preset)
        left_column.addWidget(self.project_group)

        self.rhythm_group = QGroupBox(self.tr('Rhythm'))
        rhythm_form = QFormLayout(self.rhythm_group)
        self._configure_form_layout(rhythm_form)

        self.rhythm_disabled = QCheckBox(self.tr('Disable swing / groove'))
        self.rhythm_disabled.toggled.connect(self._update_rhythm_mode)
        rhythm_form.addRow(self.rhythm_disabled)

        self.swing_preset = QComboBox()
        self.swing_preset.setAccessibleName(self.tr('Swing preset'))
        self._expand_form_field(self.swing_preset)
        rhythm_form.addRow(self.tr('Swing preset'), self.swing_preset)

        self.groove_preset = QComboBox()
        self.groove_preset.setAccessibleName(self.tr('Groove preset'))
        self._expand_form_field(self.groove_preset)
        rhythm_form.addRow(self.tr('Groove preset'), self.groove_preset)

        self.force_swing = QCheckBox(self.tr('Force swing when score has no Swing marking'))
        rhythm_form.addRow(self.force_swing)

        self.force_groove = QCheckBox(self.tr('Force groove when score has no Groove marking'))
        rhythm_form.addRow(self.force_groove)

        rhythm_help = QLabel(self.tr(
            'Swing applies when a “Swing” text expression is present in the score (not title or lyrics), '
            'or when Force swing is enabled. Groove applies when a “Groove” marking is present and a groove '
            'preset is selected, or when Force groove is enabled. Groove overrides swing when both apply.',
        ))
        rhythm_help.setObjectName('formHelpText')
        rhythm_help.setWordWrap(True)
        rhythm_form.addRow(rhythm_help)
        left_column.addWidget(self.rhythm_group)
        left_column.addStretch()

        self.custom_tracks_group = QGroupBox(self.tr('Custom per-track settings'))
        custom_layout = QVBoxLayout(self.custom_tracks_group)
        custom_layout.setContentsMargins(*_FORM_MARGINS)
        custom_layout.setSpacing(_FORM_V_SPACING)
        self.custom_tracks = QCheckBox(self.tr('Override track preset with custom rows'))
        self.custom_tracks.toggled.connect(self._update_track_mode)
        custom_layout.addWidget(self.custom_tracks)

        tracks_layout = QVBoxLayout()
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        tracks_layout.setSpacing(_FORM_V_SPACING)

        self.track_view = QTableView()
        self.track_view.setModel(self.track_model)
        self.track_view.setMinimumHeight(120)
        self.track_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.track_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        configure_track_table_columns(self.track_view)
        self.track_view.setAccessibleName(self.tr('Custom track settings'))
        self.track_view.setItemDelegateForColumn(1, VoiceIdDelegate(self.track_model.voice_ids, self.track_view))
        self.track_view.setItemDelegateForColumn(2, DoubleSpinDelegate(-100, 100, self.track_view))
        self.track_view.setItemDelegateForColumn(3, DoubleSpinDelegate(-10, 10, self.track_view))
        tracks_layout.addWidget(self.track_view)

        track_btn_row = QHBoxLayout()
        track_btn_row.setSpacing(8)
        add_track = QPushButton(self.tr('Add track'))
        add_track.clicked.connect(self._add_track_row)
        remove_track = QPushButton(self.tr('Remove selected'))
        remove_track.clicked.connect(self._remove_track_row)
        track_btn_row.addWidget(add_track)
        track_btn_row.addWidget(remove_track)
        track_btn_row.addStretch()
        tracks_layout.addLayout(track_btn_row)
        custom_layout.addLayout(tracks_layout)
        right_column.addWidget(self.custom_tracks_group)

        self.after_conversion_group = QGroupBox(self.tr('After conversion'))
        after_layout = QVBoxLayout(self.after_conversion_group)
        after_layout.setContentsMargins(*_FORM_MARGINS)
        after_layout.setSpacing(_FORM_V_SPACING)
        self.debug_box = QCheckBox(self.tr('Debug logging'))
        after_layout.addWidget(self.debug_box)
        self.open_utau_box = QCheckBox(self.tr('Open in OpenUtau after conversion'))
        self.open_utau_box.setToolTip(
            self.tr('Configure the OpenUtau executable via File → Set OpenUtau path…'),
        )
        after_layout.addWidget(self.open_utau_box)
        right_column.addWidget(self.after_conversion_group)
        right_column.addStretch()

        columns.addWidget(self._options_left, 1)
        columns.addWidget(self._options_right, 1)
        layout.addLayout(columns, 1)

        self._options_left.setMinimumWidth(420)
        self._options_right.setMinimumWidth(420)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.convert_btn = QPushButton(self.tr('Convert'))
        self.convert_btn.setDefault(True)
        self.cancel_btn = QPushButton(self.tr('Cancel'))
        self.cancel_btn.setEnabled(False)
        open_out = QPushButton(self.tr('Open output folder'))
        open_out.clicked.connect(self._open_output_folder)
        btn_row.addWidget(self.convert_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(open_out)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat(self.tr('Ready'))
        self.progress.setAccessibleName(self.tr('Conversion progress'))
        layout.addWidget(self.progress)

        self._update_mode_ui()
        self._update_track_mode()
        self._update_rhythm_mode()
        self._update_output_mode()

    @staticmethod
    def _configure_form_layout(form: QFormLayout) -> None:
        form.setContentsMargins(*_FORM_MARGINS)
        form.setHorizontalSpacing(_FORM_H_SPACING)
        form.setVerticalSpacing(_FORM_V_SPACING)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    @staticmethod
    def _expand_form_field(widget: QLineEdit | QComboBox) -> None:
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        widget.setMinimumWidth(140)

    def form_state(self) -> ConvertFormState:
        """Capture the current form as a view-model snapshot."""
        files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        return ConvertFormState(
            batch_mode=self.mode_dir.isChecked(),
            input_path=self.input_path.text().strip(),
            input_files=files,
            auto_output=self.auto_output.isChecked(),
            output_path=self.output_path.text().strip(),
            project_name=self.project_name.text().strip() or self.tr('New Project'),
            track_preset_id=self.track_preset.currentText() or None,
            swing_preset_id=self._selected_preset_id(self.swing_preset),
            groove_preset_id=self._selected_preset_id(self.groove_preset),
            rhythm_disabled=self.rhythm_disabled.isChecked(),
            force_swing=self.force_swing.isChecked(),
            force_groove=self.force_groove.isChecked(),
            use_custom_tracks=self.custom_tracks.isChecked(),
            custom_tracks=self.track_model.rows(),
            debug=self.debug_box.isChecked(),
            open_in_openutau=self.open_utau_box.isChecked(),
        )

    def collect_options(self) -> NativeUiOptions:
        """Build validated conversion options (compat wrapper for tests)."""
        openutau_path = self._settings.get_openutau_path().strip() or None
        return build_native_ui_options(
            self.form_state(),
            self._config_path_provider(),
            openutau_path=openutau_path,
        )

    def apply_settings(self, settings: UiSettings) -> None:
        """Restore convert-tab preferences from persistent storage."""
        batch_mode = settings.get_bool('batch_mode')
        self.mode_dir.setChecked(batch_mode)
        self.mode_single.setChecked(not batch_mode)

        last_input = settings.get_str('last_input_path')
        if last_input:
            self.input_path.setText(last_input)

        preset = settings.get_str('track_preset')
        if preset:
            idx = self.track_preset.findText(preset)
            if idx >= 0:
                self.track_preset.setCurrentIndex(idx)

        self._select_preset_combo(self.swing_preset, settings.get_str('swing_preset'), default='default')
        self._select_preset_combo(self.groove_preset, settings.get_str('groove_preset'), default=NONE_PRESET_ID)

        self.rhythm_disabled.setChecked(settings.get_bool('rhythm_disabled'))
        self.force_swing.setChecked(settings.get_bool('force_swing'))
        self.force_groove.setChecked(settings.get_bool('force_groove'))

        self.debug_box.setChecked(settings.get_bool('debug'))
        self.open_utau_box.setChecked(settings.get_bool('open_in_openutau'))

        project_name = settings.get_str('project_name')
        if project_name:
            self.project_name.setText(project_name)

        self.custom_tracks.setChecked(settings.get_bool('use_custom_tracks'))

        self._update_mode_ui()
        self._update_rhythm_mode()
        self._update_track_mode()

    def save_settings(self, settings: UiSettings) -> None:
        """Persist convert-tab preferences."""
        state = self.form_state()
        settings.set_bool('batch_mode', state.batch_mode)
        settings.set_str('last_input_path', state.input_path)
        settings.set_str('track_preset', state.track_preset_id or '')
        settings.set_str('swing_preset', state.swing_preset_id or '')
        settings.set_str('groove_preset', state.groove_preset_id or '')
        settings.set_bool('rhythm_disabled', state.rhythm_disabled)
        settings.set_bool('force_swing', state.force_swing)
        settings.set_bool('force_groove', state.force_groove)
        settings.set_str('project_name', state.project_name)
        settings.set_bool('use_custom_tracks', state.use_custom_tracks)
        settings.set_bool('debug', state.debug)
        settings.set_bool('open_in_openutau', state.open_in_openutau)

    def log_line(self, message: str) -> None:
        """Append a timestamped line to the session conversion log."""
        self._conversion_log.append(message)

    def set_busy(self, busy: bool) -> None:
        """Enable or disable controls while a conversion runs."""
        self.convert_btn.setEnabled(not busy)
        self.cancel_btn.setEnabled(busy)
        self.drop_frame.setEnabled(not busy)

    def set_progress(self, current: int, total: int, message: str | None = None) -> None:
        """Update the progress bar."""
        if total <= 0:
            self.progress.setRange(0, 0)
            self.progress.setFormat(message or self.tr('Working…'))
            return
        self.progress.setRange(0, total)
        self.progress.setValue(current)
        label = message or self.tr('%v / %m files')
        self.progress.setFormat(label)

    def reset_progress(self) -> None:
        """Reset the progress bar to the idle state."""
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.progress.setFormat(self.tr('Ready'))

    def reload_config_metadata(self) -> None:
        """Reload voice ids and track presets from the active config file."""
        path = self._config_path_provider()
        try:
            app_cfg = parse_config(path)
            self._voice_ids = sorted(app_cfg.voice_config_map.keys())
            self.track_model.set_voice_ids(self._voice_ids)
            presets = list_track_config_ids(path)
            current = self.track_preset.currentText()
            self.track_preset.clear()
            self.track_preset.addItems(presets)
            if current in presets:
                self.track_preset.setCurrentText(current)
            elif presets:
                self.track_preset.setCurrentIndex(0)

            swing_presets = list_swing_preset_ids(path)
            groove_presets = list_groove_preset_ids(path)
            self._reload_preset_combo(
                self.swing_preset,
                swing_presets,
                current_id=self._selected_preset_id(self.swing_preset),
                default_id='default' if 'default' in swing_presets else (swing_presets[0] if swing_presets else NONE_PRESET_ID),
            )
            self._reload_preset_combo(
                self.groove_preset,
                groove_presets,
                current_id=self._selected_preset_id(self.groove_preset),
                default_id=NONE_PRESET_ID,
            )
        except Exception as exc:
            self.log_line(f'{self.tr("Config metadata")}: {exc}')

    def _reload_preset_combo(
            self,
            combo: QComboBox,
            preset_ids: list[str],
            *,
            current_id: str | None,
            default_id: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(self.tr(NONE_PRESET_LABEL), NONE_PRESET_ID)
        for preset_id in preset_ids:
            combo.addItem(preset_id, preset_id)
        combo.blockSignals(False)

        target = current_id if current_id in preset_ids else default_id
        index = combo.findData(target)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentIndex(0)

    def _select_preset_combo(self, combo: QComboBox, preset_id: str, *, default: str) -> None:
        target = preset_id or default
        index = combo.findData(target)
        if index < 0 and target != NONE_PRESET_ID:
            index = combo.findText(target)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _selected_preset_id(self, combo: QComboBox) -> str | None:
        data = combo.currentData()
        if data in (None, NONE_PRESET_ID):
            return None
        return str(data)

    def _update_rhythm_mode(self) -> None:
        enabled = not self.rhythm_disabled.isChecked()
        self.swing_preset.setEnabled(enabled)
        self.groove_preset.setEnabled(enabled)
        self.force_swing.setEnabled(enabled)
        self.force_groove.setEnabled(enabled)

    def ingest_dropped_paths(self, paths: list[str]) -> None:
        """Handle files or folders dropped onto the tab."""
        if not paths:
            return
        if len(paths) == 1 and Path(paths[0]).is_dir():
            self.mode_dir.setChecked(True)
            self.input_path.setText(paths[0])
            self._scan_directory(paths[0])
            return

        files: list[str] = []
        for raw_path in paths:
            path = Path(raw_path)
            if path.is_dir():
                self.mode_dir.setChecked(True)
                self.input_path.setText(str(path))
                self._scan_directory(str(path))
                return
            if is_supported_input(path):
                files.append(str(path.resolve()))

        if files:
            self.mode_single.setChecked(True)
            self.file_list.clear()
            self.file_list.addItems(files)
            self.input_path.setText(files[0])
            if self.auto_output.isChecked() and len(files) == 1:
                self.output_path.setText(to_output_file(files[0]))
            self._update_output_mode()

    def remember_last_output(self, outputs: list[str]) -> None:
        """Store the directory of the most recent output for folder open."""
        if outputs:
            self._last_output_dir = str(Path(outputs[0]).parent)
            self._settings.set_str('last_output_dir', self._last_output_dir)

    def open_input_browser(self) -> None:
        """Open the input file/directory browser (menu shortcut)."""
        self._browse_input()

    def _update_mode_ui(self) -> None:
        dir_mode = self.mode_dir.isChecked()
        self.file_list.setVisible(not dir_mode)
        if dir_mode and self.input_path.text():
            self._scan_directory(self.input_path.text())
        self._update_output_mode()

    def _update_track_mode(self) -> None:
        custom = self.custom_tracks.isChecked()
        self.track_preset.setEnabled(not custom)
        self.track_view.setEnabled(custom)
        if custom and self.track_model.rowCount() == 0:
            self._add_track_row()

    def _update_output_mode(self) -> None:
        multi = self.file_list.count() > 1
        manual_allowed = not multi and not self.mode_dir.isChecked()
        if multi or self.mode_dir.isChecked():
            self.auto_output.setChecked(True)
        self.auto_output.setEnabled(manual_allowed)
        self.output_path.setEnabled(manual_allowed and not self.auto_output.isChecked())

    def _dialog_start_dir(self, fallback: str | None = None) -> str:
        for candidate in (
            fallback,
            self._settings.get_str('last_input_path'),
            self._settings.get_str('last_output_dir'),
            str(Path.home()),
        ):
            if candidate and Path(candidate).exists():
                path = Path(candidate)
                return str(path if path.is_dir() else path.parent)
        return str(Path.home())

    def _browse_input(self) -> None:
        start = self._dialog_start_dir(self.input_path.text().strip() or None)
        if self.mode_dir.isChecked():
            path = QFileDialog.getExistingDirectory(self, self.tr('Input directory'), start)
            if path:
                self.input_path.setText(path)
                self._scan_directory(path)
        else:
            paths, _ = QFileDialog.getOpenFileNames(
                self, self.tr('Input files'), start, INPUT_FILTER)
            if paths:
                self.file_list.clear()
                self.file_list.addItems(paths)
                self.input_path.setText(paths[0])
                if self.auto_output.isChecked() and len(paths) == 1:
                    self.output_path.setText(to_output_file(paths[0]))
                self._update_output_mode()

    def _browse_output(self) -> None:
        start = self._dialog_start_dir(self.output_path.text().strip() or None)
        path, _ = QFileDialog.getSaveFileName(self, self.tr('Output USTX'), start, USTX_FILTER)
        if path:
            if not path.lower().endswith('.ustx'):
                path += '.ustx'
            self.output_path.setText(path)
            self.auto_output.setChecked(False)
            self._update_output_mode()

    def _scan_directory(self, directory: str) -> None:
        files = get_input_files_from_dir(directory)
        self.file_list.clear()
        self.file_list.addItems(files)
        self.log_line(self.tr('Found {count} file(s) in {directory}').format(
            count=len(files),
            directory=directory,
        ))

    def _add_track_row(self) -> None:
        self.track_model.add_row()

    def _remove_track_row(self) -> None:
        index = self.track_view.currentIndex()
        if index.isValid():
            self.track_model.remove_row(index.row())

    def _open_output_folder(self) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        folder = self._last_output_dir or self._settings.get_str('last_output_dir') or None
        if not folder:
            text = self.output_path.text().strip()
            if text:
                folder = str(Path(text).parent)
            elif self.file_list.count():
                folder = str(Path(self.file_list.item(0).text()).parent)
        if folder and Path(folder).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
