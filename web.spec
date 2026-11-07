# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Family Tree Web."""

import os

block_cipher = None

# Get absolute paths - use os.getcwd() for spec files
base_dir = os.getcwd()
src_dir = os.path.join(base_dir, 'src')

a = Analysis(
    ['src/familytree/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(src_dir, 'familytree', 'templates'), 'familytree/templates'),
        (os.path.join(src_dir, 'familytree', 'static'), 'familytree/static'),
    ],
    hiddenimports=[
        'familytree.main',
        'familytree.core.database',
        'familytree.core.config',
        'familytree.core.templates',
        'familytree.infrastructure.db.models',
        'familytree.infrastructure.db.repositories.person_repo',
        'familytree.api.v1.endpoints.pages',
        'familytree.api.v1.endpoints.persons',
        'familytree.schemas.person',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PyQt5', 'PySide6'],
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
    name='family_tree_web',
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
