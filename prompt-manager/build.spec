# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('icon-rounded.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuickWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtSensors',
        'PySide6.QtPositioning',
        'PySide6.QtLocation',
        'PySide6.QtWebChannel',
        'PySide6.QtWebSockets',
        'PySide6.QtSql',
        'PySide6.QtTest',
        'PySide6.QtXml',
        'PySide6.QtHelp',
        'PySide6.QtUiTools',
        'PySide6.QtDesigner',
        'PySide6.QtScript',
        'PySide6.QtScriptTools',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtWinExtras',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

_common = dict(
    name='PromptManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if sys.platform == 'darwin':
    # macOS：onedir + .app 包（onefile 配 .app 会被 PyInstaller 判为不建议用法，
    # 且每次启动都要把依赖解压到临时目录，冷启动明显更慢）
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        icon='icon-rounded.icns',
        **_common,
    )
    coll = COLLECT(exe, a.binaries, a.datas, name='PromptManager')
    app = BUNDLE(
        coll,
        name='PromptManager.app',
        icon='icon-rounded.icns',
        bundle_identifier='com.zhangyunfang.promptmanager',
        info_plist={
            'CFBundleName': '提示词管理',
            'CFBundleDisplayName': '提示词管理',
            'CFBundleShortVersionString': '1.6.2',
            'CFBundleVersion': '1.6.2',
            'NSHighResolutionCapable': True,
        },
    )
else:
    # Windows / Linux：onedir（文件夹版）。
    # 早先是单文件，但单文件启动时要把 PySide6/Qt6Core.dll 等从 exe 里解压到临时目录，
    # 杀软拦截或受限的临时目录会让这一步失败，报
    # "Failed to extract PySide6\Qt6Core.dll decompression resulted in return code -1"。
    # 文件夹版没有任何运行时解压步骤，这类报错就不可能再出现。
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        icon='icon-rounded.ico',
        **_common,
    )
    coll = COLLECT(exe, a.binaries, a.datas, name='PromptManager')
