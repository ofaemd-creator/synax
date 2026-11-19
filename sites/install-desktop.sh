#!/usr/bin/env bash
set -euo pipefail
echo "=================================================================="
echo "  SYNAX Studio & 3D Pixar-Tycoon Agent Office v4.0 — Desktop Setup"
echo "=================================================================="
INSTALL_DIR="$HOME/.synax-desktop"
rm -rf "$INSTALL_DIR"
git clone --depth 1 https://github.com/ofaemd-creator/synax-agent-office.git "$INSTALL_DIR"
if [ "$(uname -s)" = "Darwin" ] && [ -f "$INSTALL_DIR/SYNAX-Desktop-macOS-v4.0.0.zip" ]; then
  unzip -qo "$INSTALL_DIR/SYNAX-Desktop-macOS-v4.0.0.zip" -d /Applications/ || true
  unzip -qo "$INSTALL_DIR/SYNAX-Desktop-macOS-v4.0.0.zip" -d "$HOME/Desktop/" || true
  echo "✓ Installed SYNAX Studio.app to /Applications and ~/Desktop!"
fi
python3 "$INSTALL_DIR/src/synax/office_mcp_server.py" --install-integrations || true
nohup python3 "$INSTALL_DIR/src/synax/agent_office.py" --serve --port 8795 >/tmp/synax_desktop.log 2>&1 &
sleep 1
open "http://127.0.0.1:8795" 2>/dev/null || xdg-open "http://127.0.0.1:8795" 2>/dev/null || true
echo "🎉 SYNAX Studio v4.0 is now running on your computer at http://127.0.0.1:8795 !"
