# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 6.x — run from repo root:  pyinstaller jarvis.spec
from __future__ import annotations

import pathlib

# SPECPATH is provided by PyInstaller when it runs this file
ROOT = pathlib.Path(SPECPATH).resolve()  # type: ignore[name-defined]

_datas: list[tuple[str, str]] = []
_asset_dir = ROOT / "jarvis" / "assets"
if _asset_dir.is_dir():
    _datas.append((str(_asset_dir), "jarvis/assets"))
# Bundled next to the app in the PyInstaller extract dir (load_dotenv in jarvis.utils.config)
for _env_name in (".env", ".env.example"):
    _p = ROOT / _env_name
    if _p.is_file():
        _datas.append((str(_p), "."))

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
        "PIL._imaging",
        "comtypes",
        "comtypes.client",
        "pycaw",
        "pycaw.api",
        "pyttsx3",
        "pyttsx3.drivers",
        "pyttsx3.drivers.sapi5",
        "speech_recognition",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Jarvis",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
