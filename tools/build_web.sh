#!/usr/bin/env bash
# Build the browser (pygbag/WebAssembly) bundle from a clean copy of the game.
#
# Packaging the repo root directly ships whatever is lying around in it: the
# April 2026 itch.io build carried a developer's local save.json, the READMEs
# and the Makefile. Staging copies only what the game loads.
#
#   tools/build_web.sh          -> build/web/ (index.html, shadowmario.apk) and build/web.zip
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
STAGE_PARENT="$ROOT/build/web-src"
STAGE="$STAGE_PARENT/shadowmario"

rm -rf "$STAGE_PARENT" "$ROOT/build/web" "$ROOT/build/web.zip"
mkdir -p "$STAGE"
cp "$ROOT/main.py" "$STAGE/"
cp -R "$ROOT/shadow_mario" "$ROOT/res" "$STAGE/"
find "$STAGE" -name __pycache__ -type d -prune -exec rm -rf {} +

"$PYTHON" -m pygbag --build --archive --ume_block 0 --disable-sound-format-error "$STAGE"

mv "$STAGE/build/web" "$ROOT/build/web"
mv "$STAGE/build/web.zip" "$ROOT/build/web.zip"
echo "web bundle: $ROOT/build/web ($(du -sh "$ROOT/build/web" | cut -f1))"
