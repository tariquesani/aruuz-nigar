# -*- mode: python ; coding: utf-8 -*-
# pyinstaller spec file for Aruuz Nigar
# Run with: pyinstaller --clean --noconfirm aruuznigar.spec
# Read RELEASING.md before compiling

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

block_cipher = None

def _include_mcp_submodule(name: str) -> bool:
    # mcp.cli requires typer (optional); launcher only needs server/SSE runtime.
    return not name.startswith("mcp.cli")


_mcp_hiddenimports = (
    collect_submodules("mcp", filter=_include_mcp_submodule)
    + collect_submodules("fastmcp")
    + collect_submodules("rich._unicode_data")
)

# fastmcp reads __version__ via importlib.metadata at import time
_mcp_datas = copy_metadata("fastmcp", recursive=True) + copy_metadata("mcp")

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("web\\templates", "web\\templates"),
        ("web\\static", "web\\static"),
        ("aruuz", "aruuz"),
        ("mcp\\aruuznigar.py", "mcp"),
    ]
    + _mcp_datas,
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
    excludes=["mcp.cli"],
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
