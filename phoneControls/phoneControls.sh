#!/bin/bash

# === CONFIG ===
SERVER_DIR="..."
OVERLAY_DIR="..."
NVM_INIT="$HOME/.nvm/nvm.sh"
SERVER_LOG="$SERVER_DIR/webServer.log"
SYSLOG_LOG="$SERVER_DIR/syslogServer.log"
OVERLAY_LOG="$OVERLAY_DIR/overlay.log"

# === DETECT PROCESSES ===
SERVER_PID=$(pgrep -f "python3 webServer.py")
SYSLOG_PID=$(pgrep -f "python3 syslogServer.py")
ELECTRON_PIDS=$(pgrep -f "electron")

# === TOGGLE LOGIC ===
if [[ -n "$SERVER_PID" || -n "$SYSLOG_PID" || -n "$ELECTRON_PIDS" ]]; then
  echo "[TOGGLE] Stopping server, syslog, and overlay..."

  if [[ -n "$SERVER_PID" ]]; then
    echo "  [STOP] Killing webServer.py (PID: $SERVER_PID)"
    kill "$SERVER_PID"
  fi

  if [[ -n "$SYSLOG_PID" ]]; then
    echo "  [STOP] Killing syslogServer.py (PID: $SYSLOG_PID)"
    kill "$SYSLOG_PID"
  fi

  if [[ -n "$ELECTRON_PIDS" ]]; then
    echo "  [STOP] Killing Electron overlay processes:"
    for pid in $ELECTRON_PIDS; do
      echo "    → Killing PID $pid"
      kill "$pid"
    done
  fi

  echo "[TOGGLE] Shutdown complete."
else
  echo "[TOGGLE] Starting server, syslog, and overlay..."

  # === START SERVER ===
  cd "$SERVER_DIR"
  echo "  [START] Launching Python webServer.py..."
  python3 webServer.py >> "$SERVER_LOG" 2>&1 &
  sleep 1

  echo "  [START] Launching Python syslogServer.py..."
  python3 syslogServer.py >> "$SYSLOG_LOG" 2>&1 &
  sleep 1

  # === INIT NVM AND START OVERLAY ===
  echo "  [START] Initializing NVM..."
  export NVM_DIR="$HOME/.nvm"
  source "$NVM_INIT"

  cd "$OVERLAY_DIR"
  echo "  [START] Launching Electron overlay..."
  npm start >> "$OVERLAY_LOG" 2>&1 &
fi
