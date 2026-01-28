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

# When running from source, `python/` is the app directory.
# When running from PyInstaller onefile, `BASE_DIR` is the extraction root.
if hasattr(sys, "_MEIPASS"):
    PROJECT_ROOT = BASE_DIR
else:
    PROJECT_ROOT = BASE_DIR.parent

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

# ------------------------------------------------------------
# Import Flask app AFTER paths are resolved
# ------------------------------------------------------------
from app import app   # <-- change 'myapp' to your Flask module

# ------------------------------------------------------------
# Flask runner (no reloader, no debug)
# ------------------------------------------------------------
def run_flask():
    print("[launcher] Starting Flask server...")
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )

# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    print("[launcher] Launching Aruuz Nigar")

    # Start Flask in background thread
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    # Give Flask a moment to start
    time.sleep(1.5)

    url = "http://127.0.0.1:5000"
    print(f"[launcher] Opening browser at {url}")
    webbrowser.open(url)

    # Keep the process alive (console stays open)
    t.join()
