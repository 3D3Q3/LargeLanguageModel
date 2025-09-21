# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for the Genius automation assistant."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = Path(__file__).resolve().parent
ICON_PATH = SPEC_DIR / "artifacts" / "genius.ico"

DATA_FILES = [
    (str(PROJECT_ROOT / "genius_config.yaml"), "config/genius_config.yaml"),
    (str(PROJECT_ROOT / "LICENSE"), "docs/LICENSE.txt"),
    (str(PROJECT_ROOT / "README.md"), "docs/README.md"),
]

HIDDEN_IMPORTS = [
    "pystray._win32",
    "win10toast",
]

block_cipher = None


a = Analysis(
    [str(PROJECT_ROOT / "genius" / "__main__.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=DATA_FILES,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="Genius",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=str(ICON_PATH) if ICON_PATH.exists() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Genius",
)
