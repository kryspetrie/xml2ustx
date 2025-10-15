import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QPushButton, QLabel, QVBoxLayout, QWidget, QMenuBar, QAction, QTextEdit, QDialog, QMessageBox, QHBoxLayout, QCheckBox, QScrollArea, QSizePolicy, QGridLayout, QFrame
)
import subprocess
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'src' 'resources', 'config.yml')

class CollapsibleSection(QWidget):
    def __init__(self, title, description, is_optional=True, repeatable=False, expanded=False, show_checkbox=True, repeatable_widget_type=None):
        super().__init__()
        self.header_label = QLabel(f"<b>{title}</b>: {description}{' <i>(optional)</i>' if is_optional else ''}")
        self.header_label.setWordWrap(True)
        self.header_label.setStyleSheet('padding: 4px;')
        self.toggle_btn = QPushButton()
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(expanded)
        self.toggle_btn.setFixedWidth(20)
        self.toggle_btn.setText('▼' if expanded else '▶')
        self.toggle_btn.setStyleSheet('border: none;')
        self.toggle_btn.toggled.connect(self.toggle_content)
        self.header_layout = QHBoxLayout()
        self.header_layout.addWidget(self.toggle_btn)
        if show_checkbox:
            self.enabled_checkbox = QCheckBox('Enable')
            self.enabled_checkbox.setChecked(expanded)
            self.header_layout.addWidget(self.enabled_checkbox)
        self.header_layout.addWidget(self.header_label, stretch=1)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_widget = QWidget()
        self.header_widget.setLayout(self.header_layout)
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.inputs = []
        self.repeatable = repeatable
        self.repeatable_widget_type = repeatable_widget_type
        # Do NOT create a QLineEdit here. Only child widgets should add their own input if needed.
        self.content_widget = QWidget()
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setVisible(expanded)
        self.content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        if not expanded:
            self.content_widget.setMaximumHeight(0)
            self.setMaximumHeight(self.header_widget.sizeHint().height() + 8)
        else:
            self.content_widget.setMaximumHeight(4320)
            self.setMaximumHeight(4320)
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.header_widget)
        self.main_layout.addWidget(self.content_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

    def toggle_content(self, checked):
        self.content_widget.setVisible(checked)
        self.toggle_btn.setText('▼' if checked else '▶')
        if checked:
            self.content_widget.setMaximumHeight(4320)  # 8K monitor vertical resolution
            self.setMaximumHeight(4320)
        else:
            self.content_widget.setMaximumHeight(0)
            self.setMaximumHeight(self.header_widget.sizeHint().height() + 8)

    def isChecked(self):
        return self.enabled_checkbox.isChecked() if hasattr(self, 'enabled_checkbox') else True

    def get_value(self):
        # Only return value if a child widget has an input
        if not self.isChecked():
            return None
        # This will only work if a child widget sets self.input
        val = getattr(self, 'input', None)
        if val:
            return val.text().strip() or None
        return None

    def get_values(self):
        if hasattr(self, 'inputs'):
            vals = []
            for widget in self.inputs:
                if isinstance(widget, QtWidgets.QSlider):
                    if widget.minimum() == -100 and widget.maximum() == 100:
                        vals.append(widget.value())
                    elif widget.minimum() == -10 and widget.maximum() == 10:
                        vals.append(widget.value()/10.0)
                elif isinstance(widget, QtWidgets.QLineEdit):
                    val = widget.text().strip()
                    if val:
                        vals.append(val)
            return vals
        return []

    def add_repeatable_row(self):
        # Add a widget based on repeatable_widget_type
        if self.repeatable_widget_type == 'slider_pan':
            slider_layout = QVBoxLayout()
            pan_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            pan_slider.setMinimum(-100)
            pan_slider.setMaximum(100)
            pan_slider.setValue(0)
            pan_slider.setTickInterval(10)
            pan_slider.setSingleStep(1)
            pan_slider.setPageStep(1)
            pan_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
            slider_layout.addWidget(pan_slider)
            minmax_layout = QHBoxLayout()
            min_label = QLabel('-100')
            min_label.setAlignment(QtCore.Qt.AlignLeft)
            max_label = QLabel('100')
            max_label.setAlignment(QtCore.Qt.AlignRight)
            minmax_layout.addWidget(min_label)
            minmax_layout.addStretch(1)
            minmax_layout.addWidget(max_label)
            slider_layout.addLayout(minmax_layout)
            self.content_layout.insertLayout(self.content_layout.count()-1, slider_layout)
            self.inputs.append(pan_slider)
        elif self.repeatable_widget_type == 'slider_volume':
            slider_layout = QVBoxLayout()
            volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            volume_slider.setMinimum(-100)
            volume_slider.setMaximum(100)
            volume_slider.setValue(10)
            volume_slider.setTickInterval(10)
            volume_slider.setSingleStep(1)
            volume_slider.setPageStep(1)
            volume_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
            slider_layout.addWidget(volume_slider)
            volume_minmax_layout = QHBoxLayout()
            volume_min_label = QLabel('-10.0')
            volume_min_label.setAlignment(QtCore.Qt.AlignLeft)
            volume_max_label = QLabel('10.0')
            volume_max_label.setAlignment(QtCore.Qt.AlignRight)
            volume_minmax_layout.addWidget(volume_min_label)
            volume_minmax_layout.addStretch(1)
            volume_minmax_layout.addWidget(volume_max_label)
            slider_layout.addLayout(volume_minmax_layout)
            self.content_layout.insertLayout(self.content_layout.count()-1, slider_layout)
            self.inputs.append(volume_slider)
        elif self.repeatable_widget_type is None:
            # For tracks, add a QLineEdit
            line_edit = QtWidgets.QLineEdit()
            line_edit.setPlaceholderText('Enter track name')
            self.content_layout.insertWidget(self.content_layout.count()-1, line_edit)
            self.inputs.append(line_edit)
        else:
            # Unknown type, do nothing
            pass

class InputFileSection(QWidget):
    def __init__(self, expanded=True):
        super().__init__()
        layout = QVBoxLayout()
        self.header_label = QLabel('<b>Input File</b>: Input file to convert: [*.xml, *.musicxml, *.mxl, *.midi]')
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)
        file_btn = QPushButton('Browse')
        file_btn.clicked.connect(self.choose_file)
        layout.addWidget(file_btn)
        self.setLayout(layout)

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'MusicXML/MIDI Files (*.xml *.mxl *.mid *.musicxml)')
        if file_path:
            # Store selected file path in a property
            self.selected_file = file_path

class OutputFileSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.header_label = QLabel('<b>Output File</b>: Output file to create - example: outfile.ustx')
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)
        file_btn = QPushButton('Browse')
        file_btn.clicked.connect(self.choose_file)
        layout.addWidget(file_btn)
        self.setLayout(layout)

    def choose_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save file', '', 'USTX Files (*.ustx)')
        if file_path:
            self.selected_file = file_path

class InputDirectorySection(QWidget):
    def __init__(self, expanded=True):
        super().__init__()
        layout = QVBoxLayout()
        self.header_label = QLabel('<b>Input Directory</b>: Input directory with convertable files: [*.xml, *.musicxml, *.mxl, *.midi]')
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)
        dir_btn = QPushButton('Browse')
        dir_btn.clicked.connect(self.choose_dir)
        layout.addWidget(dir_btn)
        self.setLayout(layout)

    def choose_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Choose input directory')
        if dir_path:
            self.selected_dir = dir_path

class ProjectNameSection(QWidget):
    def __init__(self, default='My Project'):
        super().__init__()
        layout = QVBoxLayout()
        self.header_label = QLabel('<b>Project Name</b>: Name of the project, stored in the output file metadata')
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)
        self.input = QtWidgets.QLineEdit()
        self.input.setText(default)
        layout.addWidget(self.input)
        self.enabled_checkbox = QCheckBox('Enable')
        layout.addWidget(self.enabled_checkbox)
        self.setLayout(layout)

    def isChecked(self):
        return self.enabled_checkbox.isChecked()

    def get_value(self):
        if not self.isChecked():
            return None
        val = self.input.text().strip()
        return val if val else None

class ConfigFileSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.header_label = QLabel('<b>Config File</b>: Path to the config.yml file you want to use')
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText('Choose or enter config file path')
        layout.addWidget(self.input)
        self.enabled_checkbox = QCheckBox('Enable')
        layout.addWidget(self.enabled_checkbox)
        config_btn = QPushButton('Browse')
        config_btn.clicked.connect(self.choose_config_file)
        layout.addWidget(config_btn)
        self.setLayout(layout)

    def choose_config_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Choose config file', '', 'YAML Files (*.yml *.yaml)')
        if file_path:
            self.input.setText(file_path)

    def isChecked(self):
        return self.enabled_checkbox.isChecked()

    def get_value(self):
        if not self.isChecked():
            return None
        val = self.input.text().strip()
        return val if val else None

class TrackConfigSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.header_label = QLabel('<b>Track Config</b>: Track config to use for this conversion, from config.yml')
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText('Enter track config')
        layout.addWidget(self.input)
        self.enabled_checkbox = QCheckBox('Enable')
        layout.addWidget(self.enabled_checkbox)
        self.setLayout(layout)

    def isChecked(self):
        return self.enabled_checkbox.isChecked()

    def get_value(self):
        if not self.isChecked():
            return None
        val = self.input.text().strip()
        return val if val else None

class VoiceSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.header_label = QLabel('<b>Voice(s)</b>: Voice id used for each track, from config.yml')
        self.header_label.setWordWrap(True)
        layout.addWidget(self.header_label)
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText('Enter voice ids (comma-separated)')
        layout.addWidget(self.input)
        self.enabled_checkbox = QCheckBox('Enable')
        layout.addWidget(self.enabled_checkbox)
        self.setLayout(layout)

    def isChecked(self):
        return self.enabled_checkbox.isChecked()

    def get_values(self):
        if not self.isChecked():
            return []
        val = self.input.text().strip()
        return [v.strip() for v in val.split(',') if v.strip()] if val else []

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('xml2ustx Application')
        self.resize(700, 600)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        central_widget = QWidget()
        layout = QVBoxLayout()
        # Input file
        self.input_file_section = InputFileSection(expanded=True)
        self.input_file_collapsible = CollapsibleSection(
            'Input File', 'Input file to convert: [*.xml, *.musicxml, *.mxl, *.midi]', expanded=True, show_checkbox=True, repeatable=False
        )
        self.input_file_collapsible.content_widget.layout().addWidget(self.input_file_section)
        layout.addWidget(self.input_file_collapsible)
        # Input dir
        self.input_dir_section = InputDirectorySection(expanded=True)
        self.input_dir_collapsible = CollapsibleSection(
            'Input Directory', 'Input directory with convertable files: [*.xml, *.musicxml, *.mxl, *.midi]', expanded=True, show_checkbox=True, repeatable=False
        )
        self.input_dir_collapsible.content_widget.layout().addWidget(self.input_dir_section)
        layout.addWidget(self.input_dir_collapsible)
        # Ensure only one of input_file/input_dir is enabled
        self.input_file_collapsible.enabled_checkbox.toggled.connect(lambda checked: self.input_dir_collapsible.enabled_checkbox.setChecked(False) if checked else None)
        self.input_dir_collapsible.enabled_checkbox.toggled.connect(lambda checked: self.input_file_collapsible.enabled_checkbox.setChecked(False) if checked else None)
        # Output file
        self.output_file_section = OutputFileSection()
        self.output_file_collapsible = CollapsibleSection(
            'Output File', 'Output file to create - example: outfile.ustx', expanded=False, show_checkbox=True, repeatable=False
        )
        self.output_file_collapsible.content_widget.layout().addWidget(self.output_file_section)
        layout.addWidget(self.output_file_collapsible)
        # Project name
        self.project_name_section = ProjectNameSection(default='My Project')
        self.project_name_collapsible = CollapsibleSection(
            'Project Name', 'Name of the project, stored in the output file metadata', expanded=False, show_checkbox=True, repeatable=False
        )
        self.project_name_collapsible.content_widget.layout().addWidget(self.project_name_section)
        layout.addWidget(self.project_name_collapsible)
        # Config file
        self.config_file_section = ConfigFileSection()
        self.config_file_collapsible = CollapsibleSection(
            'Config File', 'Path to the config.yml file you want to use', expanded=False, show_checkbox=True, repeatable=False
        )
        self.config_file_collapsible.content_widget.layout().addWidget(self.config_file_section)
        layout.addWidget(self.config_file_collapsible)
        # Track config
        self.track_config_section = TrackConfigSection()
        self.track_config_collapsible = CollapsibleSection(
            'Track Config', 'Track config to use for this conversion, from config.yml', expanded=False, show_checkbox=True, repeatable=False
        )
        self.track_config_collapsible.content_widget.layout().addWidget(self.track_config_section)
        layout.addWidget(self.track_config_collapsible)
        # Voices
        self.voice_section = VoiceSection()
        self.voice_collapsible = CollapsibleSection(
            'Voices', 'Voice id used for each track, from config.yml', expanded=False, show_checkbox=True, repeatable=False
        )
        self.voice_collapsible.content_widget.layout().addWidget(self.voice_section)
        layout.addWidget(self.voice_collapsible)
        # Pans
        self.pan_section = CollapsibleSection(
            'Pan(s)', 'Pan setting used for each track (-100.0 to 100.0)', is_optional=True, repeatable=True, repeatable_widget_type='slider_pan', expanded=False, show_checkbox=True
        )
        self.add_pan_btn = QPushButton('Add Pan')
        self.add_pan_btn.clicked.connect(lambda _: self.pan_section.add_repeatable_row())
        self.pan_section.content_layout.addWidget(self.add_pan_btn)
        layout.addWidget(self.pan_section)
        # Volumes
        self.volume_section = CollapsibleSection(
            'Volume(s)', 'Volume setting used for each track (-10.0 to 10.0)', is_optional=True, repeatable=True, repeatable_widget_type='slider_volume', expanded=False, show_checkbox=True
        )
        self.add_volume_btn = QPushButton('Add Volume')
        self.add_volume_btn.clicked.connect(lambda _: self.volume_section.add_repeatable_row())
        self.volume_section.content_layout.addWidget(self.add_volume_btn)
        layout.addWidget(self.volume_section)
        # Tracks
        self.track_section = CollapsibleSection(
            'Track(s)', 'Name used for each track', is_optional=True, repeatable=True, repeatable_widget_type=None, expanded=False, show_checkbox=True
        )
        self.add_track_btn = QPushButton('Add Track')
        self.add_track_btn.clicked.connect(lambda _: self.track_section.add_repeatable_row())
        self.track_section.content_layout.addWidget(self.add_track_btn)
        layout.addWidget(self.track_section)
        # Debug checkbox next to Run Application
        debug_layout = QHBoxLayout()
        self.run_btn = QPushButton('Run Application')
        self.run_btn.clicked.connect(self.run_app)
        self.debug_checkbox = QCheckBox('Debug Mode')
        debug_layout.addWidget(self.run_btn)
        debug_layout.addWidget(self.debug_checkbox)
        debug_layout.addStretch(1)
        layout.addLayout(debug_layout)
        layout.addStretch(1)
        central_widget.setLayout(layout)
        scroll.setWidget(central_widget)
        self.setCentralWidget(scroll)
        menubar = self.menuBar()
        config_menu = menubar.addMenu('Config')
        edit_action = QAction('Edit config.yml', self)
        edit_action.triggered.connect(self.open_config_editor)
        config_menu.addAction(edit_action)

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'MusicXML/MIDI Files (*.xml *.mxl *.mid *.musicxml)')
        if file_path:
            self.input_file_section.input.setText(file_path)

    def choose_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Choose input directory')
        if dir_path:
            self.input_dir_section.input.setText(dir_path)

    def choose_config_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Choose config file', '', 'YAML Files (*.yml *.yaml)')
        if file_path:
            self.config_file_section.input.setText(file_path)

    def add_pan_row(self):
        slider_layout = QVBoxLayout()
        pan_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        pan_slider.setMinimum(-100)
        pan_slider.setMaximum(100)
        pan_slider.setValue(0)
        pan_slider.setTickInterval(10)
        pan_slider.setSingleStep(1)
        pan_slider.setPageStep(1)
        pan_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        slider_layout.addWidget(pan_slider)
        minmax_layout = QHBoxLayout()
        min_label = QLabel('-100')
        min_label.setAlignment(QtCore.Qt.AlignLeft)
        max_label = QLabel('100')
        max_label.setAlignment(QtCore.Qt.AlignRight)
        minmax_layout.addWidget(min_label)
        minmax_layout.addStretch(1)
        minmax_layout.addWidget(max_label)
        slider_layout.addLayout(minmax_layout)
        self.pan_section.content_layout.insertLayout(self.pan_section.content_layout.count()-1, slider_layout)
        self.pan_section.inputs.append(pan_slider)

    def add_volume_row(self):
        slider_layout = QVBoxLayout()
        volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        volume_slider.setMinimum(-100)
        volume_slider.setMaximum(100)
        volume_slider.setValue(10)
        volume_slider.setTickInterval(10)
        volume_slider.setSingleStep(1)
        volume_slider.setPageStep(1)
        volume_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        slider_layout.addWidget(volume_slider)
        volume_minmax_layout = QHBoxLayout()
        volume_min_label = QLabel('-10.0')
        volume_min_label.setAlignment(QtCore.Qt.AlignLeft)
        volume_max_label = QLabel('10.0')
        volume_max_label.setAlignment(QtCore.Qt.AlignRight)
        volume_minmax_layout.addWidget(volume_min_label)
        volume_minmax_layout.addStretch(1)
        volume_minmax_layout.addWidget(volume_max_label)
        slider_layout.addLayout(volume_minmax_layout)
        self.volume_section.content_layout.insertLayout(self.volume_section.content_layout.count()-1, slider_layout)
        self.volume_section.inputs.append(volume_slider)

    def add_track_row(self):
        line_edit = QtWidgets.QLineEdit()
        line_edit.setPlaceholderText('Enter track name')
        self.track_section.content_layout.insertWidget(self.track_section.content_layout.count()-1, line_edit)
        self.track_section.inputs.append(line_edit)

    def run_app(self):
        args = []
        # Only include enabled options
        if self.input_file_section.isChecked():
            val = self.input_file_section.get_value()
            if val:
                args += ['--input_file', val]
        if self.input_dir_section.isChecked():
            val = self.input_dir_section.get_value()
            if val:
                args += ['--input_dir', val]
        if self.output_file_section.isChecked():
            val = self.output_file_section.get_value()
            if val:
                if not val.lower().endswith('.ustx'):
                    val += '.ustx'
                args += ['--output_file', val]
        if self.project_name_section.isChecked():
            val = self.project_name_section.get_value()
            if val:
                args += ['--project_name', val]
        if self.config_file_section.isChecked():
            val = self.config_file_section.get_value()
            if val:
                args += ['--config_file', val]
        if self.track_config_section.isChecked():
            val = self.track_config_section.get_value()
            if val:
                args += ['--track_config', val]
        if self.voice_section.isChecked():
            for v in self.voice_section.get_values():
                args += ['--voice', v]
        if self.pan_section.isChecked():
            for v in self.pan_section.get_values():
                args += ['--pan', v]
        if self.volume_section.isChecked():
            for v in self.volume_section.get_values():
                args += ['--volume', v]
        if self.track_section.isChecked():
            for v in self.track_section.get_values():
                args += ['--track', v]
        if self.debug_checkbox.isChecked():
            args += ['--debug']
        # Validate input_file/input_dir
        if not (self.input_file_section.isChecked() or self.input_dir_section.isChecked()):
            QMessageBox.warning(self, 'No input', 'Please enable and set either an input file or input directory.')
            return
        if self.input_file_section.isChecked() and self.input_dir_section.isChecked():
            QMessageBox.warning(self, 'Invalid input', 'Please enable only one of input file or input directory.')
            return
        try:
            result = subprocess.run([sys.executable, 'main.py'] + args, capture_output=True, text=True, cwd=os.path.dirname(__file__))
            if result.returncode == 0:
                QMessageBox.information(self, 'Success', 'Application ran successfully.')
            else:
                QMessageBox.critical(self, 'Error', f'Error running application:\n{result.stderr}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to run application: {e}')

    def open_config_editor(self):
        dlg = ConfigEditor(self)
        dlg.exec_()

class ConfigEditor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Edit Config YAML')
        self.resize(800, 600)
        self.tabs = QtWidgets.QTabWidget()
        # Use scroll areas for both tabs
        self.voice_tab_scroll = QScrollArea()
        self.voice_tab_scroll.setWidgetResizable(True)
        self.voice_tab_content = QWidget()
        self.voice_tab_layout = QVBoxLayout()
        self.voice_tab_content.setLayout(self.voice_tab_layout)
        self.voice_tab_scroll.setWidget(self.voice_tab_content)
        self.track_tab_scroll = QScrollArea()
        self.track_tab_scroll.setWidgetResizable(True)
        self.track_tab_content = QWidget()
        self.track_tab_layout = QVBoxLayout()
        self.track_tab_content.setLayout(self.track_tab_layout)
        self.track_tab_scroll.setWidget(self.track_tab_content)
        self.tabs.addTab(self.voice_tab_scroll, 'Voice Config')
        self.tabs.addTab(self.track_tab_scroll, 'Track Config')
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        # Add control buttons
        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton('New Config')
        self.new_btn.clicked.connect(self.new_config)
        self.import_btn = QPushButton('Import Config')
        self.import_btn.clicked.connect(self.import_config)
        self.save_btn = QPushButton('Save')
        self.save_btn.clicked.connect(self.save_config)
        self.save_as_btn = QPushButton('Save As')
        self.save_as_btn.clicked.connect(self.save_as_config)
        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.save_as_btn)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
        self.voice_widgets = []
        self.track_widgets = []
        self.config_data = None
        # Always use absolute path for default config (src/resources/config.yml)
        self.config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src', 'resources', 'config.yml'))
        self.load_config(self.config_path)

    def load_config(self, path=None):
        if path:
            self.config_path = path
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = yaml.safe_load(f)
                if not self.config_data:
                    self.config_data = {'voice_config': [], 'track_config': []}
        except Exception as e:
            self.config_data = {'voice_config': [], 'track_config': []}
            QMessageBox.critical(self, 'Error', f'Failed to load config file: {self.config_path}\n{e}')
        self.refresh_voice_tab()
        self.refresh_track_tab()

    def refresh_voice_tab(self):
        # Clear layout
        while self.voice_tab_layout.count():
            item = self.voice_tab_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.voice_widgets = []
        for voice in self.config_data.get('voice_config', []):
            w = self.make_voice_widget(voice)
            self.voice_widgets.append(w)
            self.voice_tab_layout.addWidget(w['group'])
        add_voice_btn = QPushButton('Add Voice')
        add_voice_btn.clicked.connect(self.add_voice)
        self.voice_tab_layout.addWidget(add_voice_btn)
        # Add stretch to push content to top
        self.voice_tab_layout.addStretch(1)

    def refresh_track_tab(self):
        # Clear layout
        while self.track_tab_layout.count():
            item = self.track_tab_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.track_widgets = []
        for track_cfg in self.config_data.get('track_config', []):
            w = self.make_track_widget(track_cfg)
            self.track_widgets.append(w)
            self.track_tab_layout.addWidget(w['group'])
        add_track_btn = QPushButton('Add Track Config')
        add_track_btn.setStyleSheet('margin-top: 12px; margin-bottom: 12px;')
        add_track_btn.clicked.connect(self.add_track_config)
        self.track_tab_layout.addWidget(add_track_btn)
        self.track_tab_layout.addStretch(1)

    def make_track_widget(self, track_cfg, show_remove_btn=True):
        title = track_cfg.get('id', 'Unnamed')
        section = CollapsibleSection(
            title=f"{title}",
            description="Edit track configuration.",
            is_optional=False,
            expanded=False,
            show_checkbox=False
        )
        # Remove default QLineEdit from CollapsibleSection
        if hasattr(section, 'input'):
            section.content_layout.removeWidget(section.input)
            section.input.deleteLater()
            del section.input
        # ID field
        id_label = QLabel('ID:')
        id_edit = QtWidgets.QLineEdit(track_cfg.get('id', ''))
        id_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        id_layout = QVBoxLayout()
        id_layout.addWidget(id_label)
        id_layout.addWidget(id_edit)
        section.content_layout.addLayout(id_layout)
        def update_id():
            new_id = id_edit.text()
            section.header_label.setText(f"<b>{new_id}</b>: Edit track configuration.")
        id_edit.textChanged.connect(update_id)
        # Tracks
        track_widgets = []
        for track in track_cfg.get('tracks', []):
            track_id = track.get('track_name', title)
            t_section = CollapsibleSection(
                title=f'{track_id}',
                description='Edit track details.',
                is_optional=False,
                expanded=False,
                show_checkbox=False
            )
            # Voice ID
            voice_label = QLabel('Voice ID:')
            voice_id_edit = QtWidgets.QLineEdit(track.get('voice_id', ''))
            voice_id_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            voice_layout = QVBoxLayout()
            voice_layout.addWidget(voice_label)
            voice_layout.addWidget(voice_id_edit)
            t_section.content_layout.addLayout(voice_layout)
            # Pan
            pan_label = QLabel('<b>Pan:</b>')
            pan_label.setTextFormat(QtCore.Qt.RichText)
            pan_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            pan_slider.setMinimum(-100)
            pan_slider.setMaximum(100)
            pan_slider.setValue(int(round(track.get('pan', 0))))
            pan_slider.setTickInterval(10)
            pan_slider.setSingleStep(1)
            pan_slider.setPageStep(1)
            pan_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
            pan_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            pan_value_label = QLabel(f"Value: {int(round(track.get('pan', 0)))}")
            pan_value_label.setAlignment(QtCore.Qt.AlignCenter)
            pan_slider.valueChanged.connect(lambda val, lbl=pan_value_label: lbl.setText(f"Value: {val}"))
            def snap_pan():
                snapped = int(round(pan_slider.value()))
                pan_slider.setValue(snapped)
            pan_slider.sliderReleased.connect(snap_pan)
            pan_layout = QVBoxLayout()
            pan_layout.addWidget(pan_label)
            pan_layout.addWidget(pan_value_label)
            pan_layout.addWidget(pan_slider)
            t_section.content_layout.addLayout(pan_layout)
            # Volume
            volume_label = QLabel('<b>Volume:</b>')
            volume_label.setTextFormat(QtCore.Qt.RichText)
            volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            volume_slider.setMinimum(-100)
            volume_slider.setMaximum(100)
            volume_slider.setValue(int(round(float(track.get('volume', 1.0)) * 10)))
            volume_slider.setTickInterval(10)
            volume_slider.setSingleStep(1)
            volume_slider.setPageStep(1)
            volume_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
            volume_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            volume_value_label = QLabel(f"Value: {float(track.get('volume', 1.0)):.1f}")
            volume_value_label.setAlignment(QtCore.Qt.AlignCenter)
            volume_slider.valueChanged.connect(lambda val, lbl=volume_value_label: lbl.setText(f"Value: {val/10:.1f}"))
            def snap_volume():
                snapped = int(round(volume_slider.value() / 1) * 1)
                volume_slider.setValue(snapped)
            volume_slider.sliderReleased.connect(snap_volume)
            volume_layout = QVBoxLayout()
            volume_layout.addWidget(volume_label)
            volume_layout.addWidget(volume_value_label)
            volume_layout.addWidget(volume_slider)
            volume_minmax_layout = QHBoxLayout()
            volume_min_label = QLabel('-10.0')
            volume_max_label = QLabel('10.0')
            volume_minmax_layout.addWidget(volume_min_label)
            volume_minmax_layout.addStretch(1)
            volume_minmax_layout.addWidget(volume_max_label)
            volume_layout.addLayout(volume_minmax_layout)
            t_section.content_layout.addLayout(volume_layout)
            # Add the track section to the main section
            section.content_layout.addWidget(t_section)
            track_widgets.append(t_section)
        # Add Track button inside this config group
        add_track_btn = QPushButton('Add Track')
        add_track_btn.setStyleSheet('margin-top: 12px; margin-bottom: 12px;')
        def add_track_to_group():
            if 'tracks' not in track_cfg:
                track_cfg['tracks'] = []
            track_cfg['tracks'].append({'track_name': f'Track {len(track_cfg["tracks"])+1}'})
            self.refresh_track_tab()
        add_track_btn.clicked.connect(add_track_to_group)
        section.content_layout.addWidget(add_track_btn)
        # Add Remove button for this config group
        remove_btn = QPushButton('Remove Config Group')
        remove_btn.setStyleSheet('margin-bottom: 8px;')
        def remove_this_group():
            if section is not None:
                # Remove from UI
                section.setParent(None)
                # Remove from internal list and refresh
                for i, w in enumerate(self.track_widgets):
                    if w.get('group') == section:
                        self.track_widgets.pop(i)
                        break
                self.refresh_track_tab()
        remove_btn.clicked.connect(remove_this_group)
        section.content_layout.addWidget(remove_btn)
        # Return the widget dictionary for the track config
        return {'group': section, 'tracks': track_widgets, 'remove_btn': remove_btn}

    def update_remove_track_config_buttons(self):
        show = len(self.track_widgets) > 1
        for w in self.track_widgets:
            w['remove_btn'].setVisible(show)

    def add_track_config(self):
        w = self.make_track_widget({'id': 'New Track Config', 'tracks': []})
        self.track_widgets.append(w)
        self.track_tab_layout.insertWidget(len(self.track_widgets)-1, w['group'])
        self.update_remove_track_config_buttons()

    def remove_track_config(self, widget):
        if widget in self.track_widgets:
            group = widget.get('group')
            if group is not None and group.parent() is not None:
                self.track_tab.layout().removeWidget(group)
                group.deleteLater()
            self.track_widgets.remove(widget)
            self.update_remove_track_config_buttons()
        # Optionally, handle the case where widget is not found or already removed

    def add_track(self, track_widgets, layout):
        t_section = CollapsibleSection(
            title='New Track',
            description='Edit track details.',
            is_optional=False,
            expanded=False,
            show_checkbox=False
        )
        # Remove the first free text box under track details
        t_section.content_layout.addWidget(QLabel('Voice ID'))
        voice_id_edit = QtWidgets.QLineEdit('')
        t_section.content_layout.addWidget(voice_id_edit)
        # Pan
        pan_label_layout = QHBoxLayout()
        pan_value_label = QLabel("Pan: 0")
        pan_value_label.setFixedWidth(80)
        pan_label_layout.addWidget(pan_value_label)
        t_section.content_layout.addLayout(pan_label_layout)
        pan_slider_layout = QVBoxLayout()
        pan_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        pan_slider.setMinimum(-100)
        pan_slider.setMaximum(100)
        pan_slider.setValue(0)
        pan_slider.setTickInterval(10)
        pan_slider.setSingleStep(1)
        pan_slider.setPageStep(1)
        pan_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        pan_slider_layout.addWidget(pan_slider)
        minmax_layout = QHBoxLayout()
        min_label = QLabel('-100')
        min_label.setAlignment(QtCore.Qt.AlignLeft)
        max_label = QLabel('100')
        max_label.setAlignment(QtCore.Qt.AlignRight)
        minmax_layout.addWidget(min_label)
        minmax_layout.addStretch(1)
        minmax_layout.addWidget(max_label)
        pan_slider_layout.addLayout(minmax_layout)
        t_section.content_layout.addLayout(pan_slider_layout)
        pan_slider.valueChanged.connect(lambda val, lbl=pan_value_label: lbl.setText(f"Pan: {val}"))
        def snap_pan():
            snapped = int(round(pan_slider.value()))
            pan_slider.setValue(snapped)
        pan_slider.sliderReleased.connect(snap_pan)
        # Volume
        volume_label_layout = QHBoxLayout()
        volume_value_label = QLabel("Volume: 1.0")
        volume_value_label.setFixedWidth(100)
        volume_label_layout.addWidget(volume_value_label)
        t_section.content_layout.addLayout(volume_label_layout)
        volume_slider_layout = QVBoxLayout()
        volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        volume_slider.setMinimum(-100)
        volume_slider.setMaximum(100)
        volume_slider.setValue(10)
        volume_slider.setTickInterval(10)
        volume_slider.setSingleStep(1)
        volume_slider.setPageStep(1)
        volume_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        volume_slider_layout.addWidget(volume_slider)
        volume_minmax_layout = QHBoxLayout()
        volume_min_label = QLabel('-10.0')
        volume_max_label = QLabel('10.0')
        volume_minmax_layout.addWidget(volume_min_label)
        volume_minmax_layout.addStretch(1)
        volume_minmax_layout.addWidget(volume_max_label)
        volume_slider_layout.addLayout(volume_minmax_layout)
        t_section.content_layout.addLayout(volume_slider_layout)
        volume_slider.valueChanged.connect(lambda val, lbl=volume_value_label: lbl.setText(f"Volume: {val/10:.1f}"))
        def snap_volume():
            snapped = int(round(volume_slider.value() / 1) * 1)
            volume_slider.setValue(snapped)
        volume_slider.sliderReleased.connect(snap_volume)
        remove_btn = QPushButton('Remove Track')
        t_section.content_layout.addWidget(remove_btn)
        t_widget = {
            'group': t_section,
            'voice_id': voice_id_edit,
            'pan': pan_slider,
            'volume': volume_slider,
            'remove_btn': remove_btn
        }
        remove_btn.clicked.connect(lambda _, tw=t_widget: self.remove_track(track_widgets, tw, layout))
        track_widgets.append(t_widget)
        layout.insertWidget(len(track_widgets), t_section)

    def remove_track(self, track_widgets, t_widget, layout):
        layout.removeWidget(t_widget['group'])
        t_widget['group'].deleteLater()
        track_widgets.remove(t_widget)

    def save_config(self):
        # Collect voices
        voices = []
        for w in self.voice_widgets:
            v = {
                'id': w['id'].text().strip(),
                'singer': w['singer'].text().strip(),
                'renderer': w['renderer'].text().strip(),
                'phonemizer': w['phonemizer'].text().strip()
            }
            voices.append(v)
        # Collect track configs
        track_configs = []
        for w in self.track_widgets:
            tc = {
                'id': w['id'].text().strip(),
                'tracks': []
            }
            for t in w['tracks']:
                track = {}
                tn = t['track_name'].text().strip()
                if tn:
                    track['track_name'] = tn
                vid = t['voice_id'].text().strip()
                if vid:
                    track['voice_id'] = vid
                pan = t['pan'].text().strip()
                if pan:
                    try:
                        track['pan'] = float(pan)
                    except ValueError:
                        track['pan'] = pan
                volume = t['volume'].text().strip()
                if volume:
                    try:
                        track['volume'] = float(volume)
                    except ValueError:
                        track['volume'] = volume
                tc['tracks'].append(track)
            track_configs.append(tc)
        # Build YAML
        config = {
            'voice_config': voices,
            'track_config': track_configs
        }
        try:
            yaml_str = yaml.dump(config, sort_keys=False, allow_unicode=True)
            yaml.safe_load(yaml_str)  # Validate YAML
            with open(self.config_path, 'w') as f:
                f.write(yaml_str)
            QMessageBox.information(self, 'Saved', 'Config saved successfully.')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save config: {e}')

    def new_config(self):
        self.config_data = {'voice_config': [], 'track_config': []}
        self.refresh_voice_tab()
        self.refresh_track_tab()

    def import_config(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Import config file', '', 'YAML Files (*.yml *.yaml)')
        if file_path:
            self.load_config(file_path)
            QMessageBox.information(self, 'Imported', f'Loaded config from:\n{file_path}')

    def save_as_config(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save config as', '', 'YAML Files (*.yml *.yaml)')
        if file_path:
            self.config_path = file_path
            self.save_config()

    def make_voice_widget(self, voice):
        section = CollapsibleSection(
            title=f"Voice: {voice.get('id', '')}",
            description="Edit voice configuration.",
            is_optional=False,
            expanded=False,
            show_checkbox=False
        )
        section.content_layout.addWidget(QLabel('ID'))
        id_edit = QtWidgets.QLineEdit(voice.get('id', ''))
        section.content_layout.addWidget(id_edit)
        section.content_layout.addWidget(QLabel('Singer'))
        singer_edit = QtWidgets.QLineEdit(voice.get('singer', ''))
        section.content_layout.addWidget(singer_edit)
        section.content_layout.addWidget(QLabel('Renderer'))
        renderer_edit = QtWidgets.QLineEdit(voice.get('renderer', ''))
        section.content_layout.addWidget(renderer_edit)
        section.content_layout.addWidget(QLabel('Phonemizer'))
        phonemizer_edit = QtWidgets.QLineEdit(voice.get('phonemizer', ''))
        section.content_layout.addWidget(phonemizer_edit)
        remove_btn = QPushButton('Remove')
        section.content_layout.addWidget(remove_btn)
        widget = {
            'group': section,
            'id': id_edit,
            'singer': singer_edit,
            'renderer': renderer_edit,
            'phonemizer': phonemizer_edit,
            'remove_btn': remove_btn
        }
        remove_btn.clicked.connect(lambda: self.remove_voice(widget))
        return widget

    def add_voice(self):
        w = self.make_voice_widget({'id': '', 'singer': '', 'renderer': '', 'phonemizer': ''})
        self.voice_widgets.append(w)
        # Insert before the last two widgets: Add Voice button and stretch
        insert_index = self.voice_tab_layout.count() - 2 if self.voice_tab_layout.count() >= 2 else self.voice_tab_layout.count()
        self.voice_tab_layout.insertWidget(insert_index, w['group'])


def main():
    app = QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))  # Use OS look-and-feel
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
