# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for OfflineDarts.
Builds a single-folder standalone application.

Build command:
    pyinstaller offline_darts.spec

Or if PyInstaller is not installed:
    pip install pyinstaller
    pyinstaller offline_darts.spec
"""

import sys
from pathlib import Path

block_cipher = None

project_root = Path('.').resolve()

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include assets (sounds, etc.)
        ('assets', 'assets'),
        # Include data directory structure
        ('data', 'data'),
    ],
    hiddenimports=[
        'cv2',
        'numpy',
        'shapely',
        'shapely.geometry',
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtMultimedia',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
    ],
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
    name='OfflineDarts',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window — GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Add icon path when available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OfflineDarts',
)
