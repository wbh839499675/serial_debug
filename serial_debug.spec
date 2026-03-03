# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

# 使用当前工作目录作为项目根目录
project_root = Path(os.getcwd())

a = Analysis(
    [str('main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str('resources'), 'resources'),
    ],
    hiddenimports=[
        'PyQt5',
        'serial',
        'pandas',
        'numpy',
        'numpy.core._multiarray_umath',
        'numpy.core._multiarray_tests',
        'numpy.linalg.lapack_lite',
        'numpy.linalg._umath_linalg',
        'numpy.random.mtrand',
        'core.serial_controller',
        'core.relay_controller',
        'core.device_monitor',
        'core.tester',
        'core.analyzer',
        'models.data_models',
        'models.nmea_parser',
        'gnss.nmea_parser',
        'utils.logger',
        'utils.constants',
    ],
    hookspath=[str(project_root / 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SerialDebugTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
