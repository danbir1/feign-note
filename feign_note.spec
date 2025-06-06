# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['feign_note.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('feign icon\\*.png', 'feign icon'),  # 아이콘 리소스 추가
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='feign_note',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=false,
    console=False,
    icon='feign.ico',  # 실행파일 아이콘 지정
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='feign_note',
)
