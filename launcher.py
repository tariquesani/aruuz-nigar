import importlib.util
import threading
import time
import webbrowser
import sys
from pathlib import Path

# ------------------------------------------------------------
# Resolve base directory (works for PyInstaller and normal run)
# ------------------------------------------------------------
if hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

print(f"[launcher] BASE_DIR = {BASE_DIR}")

# App root is `python/` in dev and the PyInstaller extraction root when frozen.
# (Same convention as app.py `_resolve_project_root`.)
PROJECT_ROOT = BASE_DIR

MCP_SCRIPT = PROJECT_ROOT / "mcp" / "aruuznigar.py"
MCP_SSE_URL = "http://127.0.0.1:8765/sse"
FLASK_URL = "http://127.0.0.1:5000"

# ------------------------------------------------------------
# Optional safety checks (fail fast if bundle is incomplete)
# ------------------------------------------------------------
REQUIRED_DIRS = [
    PROJECT_ROOT / "web" / "templates",
    PROJECT_ROOT / "web" / "static",
    BASE_DIR / "aruuz",
]

for d in REQUIRED_DIRS:
    if not d.exists():
        raise RuntimeError(f"Required bundled directory missing: {d}")

if not MCP_SCRIPT.exists():
    raise RuntimeError(f"Required MCP script missing: {MCP_SCRIPT}")

# ------------------------------------------------------------
# Import Flask app AFTER paths are resolved
# ------------------------------------------------------------
from app import app

# ------------------------------------------------------------
# Load MCP server module (unique name avoids shadowing PyPI `mcp`)
# ------------------------------------------------------------
def _load_aruuz_mcp_module():
    spec = importlib.util.spec_from_file_location("aruuznigar_mcp", MCP_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load MCP module from {MCP_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


aruuz_mcp = _load_aruuz_mcp_module()

# ------------------------------------------------------------
# Server runners (no reloader, no debug)
# ------------------------------------------------------------
def run_flask():
    print("[launcher] Starting Flask server...")
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )


def run_mcp():
    print(f"[launcher] Starting MCP server (SSE {MCP_SSE_URL})...")
    aruuz_mcp.mcp.run(transport="sse", host="127.0.0.1", port=8765)

# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    print("[launcher] Launching Aruuz Nigar")

    flask_thread = threading.Thread(target=run_flask, daemon=True, name="flask")
    flask_thread.start()

    # Flask must be up before MCP tools call the API
    time.sleep(1.5)

    mcp_thread = threading.Thread(target=run_mcp, daemon=True, name="mcp")
    mcp_thread.start()

    print(f"[launcher] Opening browser at {FLASK_URL}")
    webbrowser.open(FLASK_URL)

    # Keep the process alive (console stays open)
    flask_thread.join()
