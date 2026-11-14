#!/bin/sh
# Launcher for OliveTin-lite server
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/server.py" "$@"
