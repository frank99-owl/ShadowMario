#!/usr/bin/env python3
"""Resolve the active itch.io playable channel for the current game page."""

from __future__ import annotations

import json
import os
import re
import urllib.request


def _set_output(value: str) -> None:
    output_path = os.environ["GITHUB_OUTPUT"]
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(f"channel={value}\n")


def main() -> None:
    game = os.environ["ITCH_GAME"]
    fallback = os.environ.get("ITCH_WEB_CHANNEL", "web")
    owner, slug = game.split("/", 1)
    page_url = f"https://{owner}.itch.io/{slug}"

    try:
        html = urllib.request.urlopen(page_url).read().decode("utf-8", "ignore")
        game_match = re.search(r'name="itch:path" content="games/(\d+)"', html)
        upload_match = re.search(r"https://html-classic\.itch\.zone/html/(\d+)/index\.html", html)

        if not game_match or not upload_match:
            raise RuntimeError("Could not resolve game_id or playable upload id from page")

        game_id = game_match.group(1)
        playable_upload_id = upload_match.group(1)
        api_url = f"https://itch.io/api/1/{os.environ['BUTLER_API_KEY']}/game/{game_id}/uploads"
        payload = json.loads(urllib.request.urlopen(api_url).read().decode("utf-8", "ignore"))
        uploads = payload.get("uploads", payload if isinstance(payload, list) else [])

        channel = None
        for upload in uploads:
            if str(upload.get("id")) == playable_upload_id:
                channel = upload.get("channel_name") or upload.get("channel")
                break

        if not channel:
            raise RuntimeError("Could not resolve playable channel from uploads API")

        print(f"Resolved playable channel: {channel}")
        _set_output(channel)
    except Exception as exc:
        print(f"Channel auto-detect failed: {exc}")
        print(f"Fallback channel: {fallback}")
        _set_output(fallback)


if __name__ == "__main__":
    main()
