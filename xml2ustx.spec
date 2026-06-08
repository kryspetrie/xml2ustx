# PyInstaller spec for OpenUtau sidecar bundle.
# Build: pyinstaller xml2ustx.spec
import os
import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)
app_version = os.environ.get("XML2USTX_VERSION", "0.0.0")

a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / 'src' / 'resources' / 'config.yml'), 'src/resources')],
    hiddenimports=['music21', 'yaml', 'jsonpickle', 'src.application.version', 'src.application._version'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'streamlit', 'matplotlib', 'tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='xml2ustx',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
