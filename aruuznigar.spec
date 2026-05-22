# -*- mode: python ; coding: utf-8 -*-
# pyinstaller spec file for Aruuz Nigar
# Run with: pyinstaller --clean --noconfirm aruuznigar.spec
# Read RELEASING.md before compiling

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

_mcp_hiddenimports = collect_submodules("mcp") + collect_submodules("fastmcp")

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("web\\templates", "web\\templates"),
        ("web\\static", "web\\static"),
        ("aruuz", "aruuz"),
        ("mcp\\aruuznigar.py", "mcp"),
    ],
    hiddenimports=[
        "flask",
        "jinja2",
        "markupsafe",
        "web.api.scan",
        "web.api.meter_dominant",
        "web.api.islah",
        "web.api.radeefkafiya",
        "pkgutil",
        "httpx",
        "httpcore",
        "h11",
        "anyio",
        "starlette",
        "uvicorn",
        "sse_starlette",
        "pydantic",
        "pydantic_core",
    ]
    + _mcp_hiddenimports,
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
    icon="aruuznigar.ico",
)
