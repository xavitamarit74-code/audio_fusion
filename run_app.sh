#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "No existe ./venv. Ejecuta primero: ./setup.sh" >&2
  exit 1
fi

PY="$PWD/venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "No se encuentra el intérprete en $PY." >&2
  echo "Tu entorno virtual puede estar corrupto o incompleto. Recomendado: ./setup.sh" >&2
  exit 1
fi

if ! "$PY" -c 'import uvicorn' >/dev/null 2>&1; then
  echo "No está instalado 'uvicorn' en el entorno virtual." >&2
  echo "Ejecuta: ./setup.sh" >&2
  exit 1
fi

PORT="${PORT:-8000}"
export PORT

if command -v lsof >/dev/null 2>&1; then
  for candidate in $(seq "$PORT" 8010); do
    if ! lsof -nP -iTCP:"$candidate" -sTCP:LISTEN >/dev/null 2>&1; then
      PORT="$candidate"
      export PORT
      break
    fi
  done
fi

"$PY" -m uvicorn backend.app:app --reload --port "$PORT" &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

"$PY" - <<'PY' || true
import time
import urllib.request
import os

port = os.environ.get("PORT", "8000")
url = f"http://127.0.0.1:{port}/"

deadline = time.time() + 10
while time.time() < deadline:
  try:
    with urllib.request.urlopen(url, timeout=0.5) as r:
      if 200 <= getattr(r, "status", 200) < 500:
        break
  except Exception:
    time.sleep(0.1)
PY

open "http://127.0.0.1:$PORT" >/dev/null 2>&1 || true

# Abre el navegador (macOS: open, Linux: xdg-open)
URL="http://127.0.0.1:$PORT"
echo "Servidor listo en: $URL"

if command -v open >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
fi

wait "$SERVER_PID"
