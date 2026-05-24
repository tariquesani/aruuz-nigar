#!/bin/sh
set -eu

APP_SRC="${APP_SRC:-/app/src}"
REPO_URL="${ARUUZ_GIT_REPO:?ARUUZ_GIT_REPO is required}"
REF="${ARUUZ_GIT_REF:-main}"
GUNICORN_BIND="${GUNICORN_BIND:-0.0.0.0:5000}"

repo_url_for_clone="${REPO_URL}"
if [ -n "${GIT_TOKEN:-}" ]; then
    repo_url_for_clone=$(printf '%s' "$REPO_URL" | sed "s#https://#https://${GIT_TOKEN}@#")
fi

mkdir -p "$(dirname "$APP_SRC")"

if [ -d "${APP_SRC}/.git" ]; then
    cd "$APP_SRC"
    git remote set-url origin "$repo_url_for_clone" 2>/dev/null || true
    git fetch origin --prune
    git checkout "$REF" 2>/dev/null || git checkout -B "$REF" "origin/${REF}"
    git reset --hard "origin/${REF}"
else
    # /app/src is often a bind mount; never rm -rf the mount point itself.
    mkdir -p "$APP_SRC"
    find "$APP_SRC" -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
    git clone --branch "$REF" --single-branch "$repo_url_for_clone" "$APP_SRC"
    cd "$APP_SRC"
fi

python -m pip install --no-cache-dir --upgrade pip
python -m pip install --no-cache-dir -r requirements.txt
python -m pip install --no-cache-dir -e .

# MCP defaults to 127.0.0.1; expose SSE on the container/LAN interface.
if [ -f mcp/aruuznigar.py ]; then
    sed -i 's/host="127.0.0.1"/host="0.0.0.0"/' mcp/aruuznigar.py
fi

gunicorn \
    --bind "${GUNICORN_BIND}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    app:app &
GUN_PID=$!

ready=0
i=0
while [ "$i" -lt 60 ]; do
    if curl -sf "http://127.0.0.1:5000/heartbeat" >/dev/null 2>&1; then
        ready=1
        break
    fi
    i=$((i + 1))
    sleep 1
done
if [ "$ready" -ne 1 ]; then
    echo "aruuz-entrypoint: gunicorn did not become ready on :5000" >&2
    kill -TERM "$GUN_PID" 2>/dev/null || true
    wait "$GUN_PID" 2>/dev/null || true
    exit 1
fi

python mcp/aruuznigar.py &
MCP_PID=$!

trap 'kill -TERM "$GUN_PID" "$MCP_PID" 2>/dev/null; wait "$GUN_PID" "$MCP_PID" 2>/dev/null; exit 0' INT TERM

wait "$GUN_PID"
STATUS=$?
kill -TERM "$MCP_PID" 2>/dev/null || true
wait "$MCP_PID" 2>/dev/null || true
exit "$STATUS"
