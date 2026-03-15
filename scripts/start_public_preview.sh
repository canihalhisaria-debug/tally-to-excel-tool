#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8501}"
APP_ENTRY="${APP_ENTRY:-app.py}"

if ! command -v streamlit >/dev/null 2>&1; then
  echo "Error: streamlit is not installed." >&2
  exit 1
fi

echo "Starting Streamlit on port ${PORT}..."
streamlit run "$APP_ENTRY" --server.address 0.0.0.0 --server.port "$PORT" >/tmp/streamlit-preview.log 2>&1 &
STREAMLIT_PID=$!

cleanup() {
  if kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; then
    kill "$STREAMLIT_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

for _ in {1..20}; do
  if curl -sSf "http://127.0.0.1:${PORT}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Streamlit logs: /tmp/streamlit-preview.log"

echo "Trying Cloudflare quick tunnel..."
if command -v cloudflared >/dev/null 2>&1; then
  if cloudflared tunnel --url "http://127.0.0.1:${PORT}"; then
    exit 0
  fi
fi

if [ ! -x /tmp/cloudflared ]; then
  if curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared; then
    chmod +x /tmp/cloudflared
  fi
fi

if [ -x /tmp/cloudflared ]; then
  if /tmp/cloudflared tunnel --url "http://127.0.0.1:${PORT}"; then
    exit 0
  fi
fi

echo "Cloudflare tunnel unavailable. Falling back to localtunnel (npx)..."
if command -v npx >/dev/null 2>&1; then
  npx localtunnel --port "$PORT"
  exit 0
fi

echo "No supported tunnel tool available (cloudflared or npx localtunnel)." >&2
exit 1
