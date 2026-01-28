# -*- mode: python ; coding: utf-8 -*-
# pyinstaller spec file for Aruuz Nigar
# Run with: pyinstaller --clean --noconfirm aruuznigar.spec

block_cipher = None

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("web\\templates", "web\\templates"),
        ("web\\static", "web\\static"),
        ("aruuz", "aruuz"),
    ],
    hiddenimports=[
        "flask",
        "jinja2",
        "markupsafe",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="aruuznigar",
    debug=False,
    console=True,   # set True temporarily if you want a console
    icon = "aruuznigar.ico"
)
