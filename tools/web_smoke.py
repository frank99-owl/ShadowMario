"""Boot the built browser bundle in headless Chromium and fail on a broken start.

    tools/build_web.sh && python tools/web_smoke.py

Serves build/web on 127.0.0.1 (pygbag's runtime treats a `localhost` origin as
its own dev server and looks for packages on port 8000), clicks to start, then
requires: the game's 1024x768 canvas appears, the page title becomes the game
title, no Python traceback reaches the in-page terminal, and the menu is
reached within --timeout seconds. The Python runtime itself comes from the
pygame-web CDN, so this needs network access, as a visitor's browser does.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TERMINAL_JS = """() => [...document.querySelectorAll('.xterm-rows > div')]
    .map(d => d.textContent).filter(t => t.trim())"""


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def serve(directory: Path) -> tuple[http.server.ThreadingHTTPServer, int]:
    handler = functools.partial(_QuietHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=str(ROOT / "build" / "web"))
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--screenshot", default=str(ROOT / "build" / "web-smoke.png"))
    args = parser.parse_args(argv)

    web_dir = Path(args.dir)
    if not (web_dir / "index.html").exists():
        print(f"no bundle at {web_dir}; run tools/build_web.sh first", file=sys.stderr)
        return 2

    server, port = serve(web_dir)
    started = time.monotonic()
    failure = None
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
        deadline = started + args.timeout
        clicked = False
        while time.monotonic() < deadline:
            rows = page.evaluate(TERMINAL_JS)
            if any("Traceback" in r for r in rows):
                failure = "Python traceback in page terminal:\n  " + "\n  ".join(rows[-12:])
                break
            size = page.evaluate("() => { const c = document.querySelector('canvas#canvas');"
                                 " return c ? [c.width, c.height] : null; }")
            if size == [1024, 768] and page.title() == "SHADOW MARIO":
                break
            if not clicked and time.monotonic() - started > 3:
                # pygbag waits for a user gesture before starting audio/game.
                page.mouse.click(640, 400)
                clicked = True
            page.wait_for_timeout(500)
        else:
            failure = f"game did not reach its menu within {args.timeout:.0f}s"

        if failure is None:
            page.wait_for_timeout(1500)  # let the menu render a few frames
        page.screenshot(path=args.screenshot)
        browser.close()
    server.shutdown()

    elapsed = time.monotonic() - started
    if failure:
        print(f"FAIL after {elapsed:.1f}s: {failure}", file=sys.stderr)
        return 1
    print(f"ok: menu reached in {elapsed:.1f}s; screenshot {args.screenshot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
