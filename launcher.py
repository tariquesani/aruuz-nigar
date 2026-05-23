import importlib.util
import threading
import time
import urllib.error
import urllib.request
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
FLASK_HEALTH_URL = f"{FLASK_URL}/heartbeat"
FLASK_READY_TIMEOUT_S = 30.0
FLASK_READY_POLL_INTERVAL_S = 0.25

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
    """
    Load and return the bundled MCP module from the resolved MCP_SCRIPT path.
    
    Attempts to create an import spec for the file at MCP_SCRIPT, execute it as a module, and return the loaded module object.
    
    Returns:
        module: The imported module object created from MCP_SCRIPT.
    
    Raises:
        RuntimeError: If a module spec or loader cannot be created for MCP_SCRIPT.
    """
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
    """
    Start the bundled Flask application bound to 127.0.0.1:5000.
    
    Runs the imported Flask `app` with debug and the reloader disabled.
    """
    print("[launcher] Starting Flask server...")
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )


def wait_for_flask_ready() -> None:
    """Poll Flask /heartbeat until it responds or timeout elapses."""
    deadline = time.monotonic() + FLASK_READY_TIMEOUT_S
    attempt = 0
    last_error: str | None = None

    while time.monotonic() < deadline:
        attempt += 1
        try:
            with urllib.request.urlopen(FLASK_HEALTH_URL, timeout=2) as resp:
                if resp.status == 200:
                    print(
                        f"[launcher] Flask ready at {FLASK_HEALTH_URL} "
                        f"(attempt {attempt})"
                    )
                    return
                last_error = f"HTTP {resp.status}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)

        print(f"[launcher] Flask not ready (attempt {attempt}): {last_error}")
        time.sleep(FLASK_READY_POLL_INTERVAL_S)

    raise RuntimeError(
        f"Flask did not become ready within {FLASK_READY_TIMEOUT_S:.0f}s "
        f"({FLASK_HEALTH_URL}); last error: {last_error}"
    )


def run_mcp():
    """
    Start the bundled MCP server configured to use SSE on the local interface.
    
    Starts the MCP server provided by the bundled aruuz MCP module, using Server-Sent Events transport bound to 127.0.0.1:8765. When running from a PyInstaller bundle (detected via sys._MEIPASS), suppress the rich banner to avoid unicode/module issues.
    """
    print(f"[launcher] Starting MCP server (SSE {MCP_SSE_URL})...")
    # Rich banner tables break under PyInstaller (dynamic unicode data modules).
    show_banner = not hasattr(sys, "_MEIPASS")
    aruuz_mcp.mcp.run(
        transport="sse",
        host="127.0.0.1",
        port=8765,
        show_banner=show_banner,
    )

# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    print("[launcher] Launching Aruuz Nigar")

    flask_thread = threading.Thread(target=run_flask, daemon=True, name="flask")
    flask_thread.start()

    # Flask must be up before MCP tools call the API
    wait_for_flask_ready()

    mcp_thread = threading.Thread(target=run_mcp, daemon=True, name="mcp")
    mcp_thread.start()

    print(f"[launcher] Opening browser at {FLASK_URL}")
    webbrowser.open(FLASK_URL)

    # Keep the process alive (console stays open)
    flask_thread.join()
