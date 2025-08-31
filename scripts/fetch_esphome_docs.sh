#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TP="$REPO_DIR/third_party/esphome-docs"

if [ -d "$TP/.git" ]; then
  git -C "$TP" fetch --depth 1 origin main
  git -C "$TP" checkout --force origin/main
else
  mkdir -p "$REPO_DIR/third_party"
  git clone --depth 1 https://github.com/esphome/esphome-docs.git "$TP"
fi
echo "ESPHome docs at: $(git -C "$TP" rev-parse --short HEAD)"
