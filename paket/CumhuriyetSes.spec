# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller tarifi — Windows/Linux için tek dosya, macOS için .app paketi.

Kullanım:  pyinstaller paket/CumhuriyetSes.spec --noconfirm --clean
"""

import sys
from pathlib import Path

PAKET = Path(SPECPATH)                       # noqa: F821  (PyInstaller sağlar)
KOK = PAKET.parent
AD = "CumhuriyetSesKonsolu"

# Kullanılmayan büyük Qt bileşenlerini dışarıda bırakıp paketi küçültüyoruz.
DISARIDA = [
    "tkinter", "unittest", "pydoc_data", "test", "distutils",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQml", "PySide6.Qt3DCore",
    "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtBluetooth",
    "PySide6.QtNetworkAuth", "PySide6.QtPositioning", "PySide6.QtSerialPort",
    "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtDesigner", "PySide6.QtHelp",
    "PySide6.QtOpenGL", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
]

cozumleme = Analysis(
    [str(KOK / "main.py")],
    pathex=[str(KOK)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    excludes=DISARIDA,
    noarchive=False,
)
pyz = PYZ(cozumleme.pure)

if sys.platform == "darwin":
    # macOS: önce klasör, sonra .app paketi (dmg betiği bunu kullanır)
    exe = EXE(
        pyz, cozumleme.scripts, [],
        exclude_binaries=True,
        name=AD,
        console=False,
        icon=str(PAKET / "app.icns"),
        argv_emulation=False,
    )
    coll = COLLECT(exe, cozumleme.binaries, cozumleme.datas, name=AD)
    app = BUNDLE(
        coll,
        name="Cumhuriyet Ses Konsolu.app",
        icon=str(PAKET / "app.icns"),
        bundle_identifier="tr.cumhuriyet.seskonsolu",
        info_plist={
            "CFBundleName": "Cumhuriyet Ses Konsolu",
            "CFBundleDisplayName": "Cumhuriyet Ses Konsolu",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "NSHumanReadableCopyright": "29 Ekim Cumhuriyet Bayramı ses konsolu",
        },
    )
else:
    # Windows ve Linux: tek dosya
    exe = EXE(
        pyz,
        cozumleme.scripts,
        cozumleme.binaries,
        cozumleme.datas,
        [],
        name=AD,
        console=False,
        upx=False,
        icon=str(PAKET / "app.ico") if sys.platform == "win32" else None,
    )
