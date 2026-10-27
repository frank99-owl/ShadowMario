"""Boot the built browser bundle in headless Chromium and fail on a broken start.

    tools/build_web.sh && python tools/web_smoke.py

Two checks, each must reach the game's menu:

- `build/web` as built (the page unpacks `shadowmario.tar.gz`), and
- `build/web.zip`, the file pushed to itch.io. pygbag's page only reads the
  `.apk` inside it when served from an `*.itch.zone` host and otherwise asks
  for a `.tar.gz` the zip does not contain, so the zip is unpacked to a temp
  folder with that host check forced on. This boots the exact archive
  visitors get, along the code path they get.

Both are served on 127.0.0.1 (pygbag's runtime treats a `localhost` origin as
its own dev server and looks for packages on port 8000). Each check clicks to
start, then requires: the 1024x768 game canvas appears, the page title becomes
the game title, and no Python traceback reaches the in-page terminal, within
--timeout seconds. The Python runtime comes from the pygame-web CDN, so this
needs network access, as a visitor's browser does.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import sys
import tempfile
import threading
import time
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TERMINAL_JS = """() => [...document.querySelectorAll('.xterm-rows > div')]
    .map(d => d.textContent).filter(t => t.trim())"""
# The line in pygbag's page template that picks the .apk loader on itch.io.
ITCH_HOST_CHECK = "if platform.window.location.host.find('.itch.zone')>0:"


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def serve(directory: Path) -> tuple[http.server.ThreadingHTTPServer, int]:
    handler = functools.partial(_QuietHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def unpack_as_itch(archive: Path, target: Path) -> None:
    """Unpack the itch.io zip and make its page take the itch.io (.apk) branch."""
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(target)
    index = target / "index.html"
    html = index.read_text(encoding="utf-8")
    if html.count(ITCH_HOST_CHECK) != 1:
        raise RuntimeError(
            "pygbag's page no longer has the itch.io host check this test forces; "
            "update ITCH_HOST_CHECK after reading the new template"
        )
    index.write_text(html.replace(ITCH_HOST_CHECK, "if True:  # web_smoke: itch.io branch"),
                     encoding="utf-8")


def boot(web_dir: Path, timeout: float, screenshot: Path) -> tuple[str | None, float]:
    """Return (failure or None, seconds taken)."""
    server, port = serve(web_dir)
    started = time.monotonic()
    failure = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
            deadline = started + timeout
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
                failure = f"game did not reach its menu within {timeout:.0f}s"

            if failure is None:
                page.wait_for_timeout(1500)  # let the menu render a few frames
            page.screenshot(path=str(screenshot))
            browser.close()
    finally:
        server.shutdown()
    return failure, time.monotonic() - started


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=str(ROOT / "build" / "web"),
                        help="built bundle folder (tar.gz loader); empty string skips it")
    parser.add_argument("--zip", default=str(ROOT / "build" / "web.zip"),
                        help="itch.io archive (.apk loader); empty string skips it")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--screenshot-dir", default=str(ROOT / "build"))
    args = parser.parse_args(argv)

    shots = Path(args.screenshot_dir)
    shots.mkdir(parents=True, exist_ok=True)
    checks: list[tuple[str, Path]] = []
    with tempfile.TemporaryDirectory() as tmp:
        if args.dir:
            web_dir = Path(args.dir)
            if not (web_dir / "index.html").exists():
                print(f"no bundle at {web_dir}; run tools/build_web.sh first", file=sys.stderr)
                return 2
            checks.append(("web", web_dir))
        if args.zip:
            archive = Path(args.zip)
            if not archive.exists():
                print(f"no archive at {archive}; run tools/build_web.sh first", file=sys.stderr)
                return 2
            itch_dir = Path(tmp) / "itch"
            unpack_as_itch(archive, itch_dir)
            checks.append(("itch-zip", itch_dir))

        failed = False
        for name, directory in checks:
            screenshot = shots / f"web-smoke-{name}.png"
            failure, elapsed = boot(directory, args.timeout, screenshot)
            if failure:
                failed = True
                print(f"FAIL [{name}] after {elapsed:.1f}s: {failure}", file=sys.stderr)
            else:
                print(f"ok [{name}]: menu reached in {elapsed:.1f}s; screenshot {screenshot}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
