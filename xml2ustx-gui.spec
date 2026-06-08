# PyInstaller spec for the native Qt GUI (installable app).
# Build: pyinstaller xml2ustx-gui.spec
# Output: dist/xml2ustx/ (Win/Linux) or dist/xml2ustx.app (macOS)
from pathlib import Path

import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None
root = Path(SPECPATH)
app_version = os.environ.get("XML2USTX_VERSION", "0.0.0")

pyside_datas, pyside_binaries, pyside_hiddenimports = collect_all("PySide6")

a = Analysis(
    [str(root / "native_ui.py")],
    pathex=[str(root)],
    binaries=pyside_binaries,
    datas=[
        (str(root / "src" / "resources" / "config.yml"), "src/resources"),
        (str(root / "src" / "resources" / "logo.png"), "src/resources"),
    ] + pyside_datas,
    hiddenimports=pyside_hiddenimports + ["music21", "yaml", "jsonpickle", "src.application.version", "src.application._version"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "streamlit", "matplotlib", "tkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="xml2ustx",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="xml2ustx",
)

import sys  # noqa: E402

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="xml2ustx.app",
        icon=None,
        bundle_identifier="org.xml2ustx.app",
        info_plist={
            "CFBundleName": "xml2ustx",
            "CFBundleDisplayName": "xml2ustx",
            "CFBundleVersion": app_version,
            "CFBundleShortVersionString": app_version,
            "NSHighResolutionCapable": True,
        },
    )
