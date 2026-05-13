import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent

flask = subprocess.Popen([sys.executable, "app.py"], cwd=str(BASE_DIR))
time.sleep(1.5)
mcp = subprocess.Popen([sys.executable, "mcp/aruuznigar.py"], cwd=str(BASE_DIR))

try:
    flask.wait()
finally:
    mcp.terminate()
    flask.terminate()
