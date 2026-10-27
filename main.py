"""Top-level script entrypoint for Shadow Mario."""

# The browser build (pygbag) decides which packages to preload by scanning the
# imports of this file only. Without pygame here, the game's own modules find
# an empty `pygame` module in the browser and crash at import.
import asyncio
import sys

import pygame  # noqa: F401

from shadow_mario.app import run_game


if __name__ == "__main__":
    # In the browser asyncio.run() schedules the game and returns at once;
    # exiting there would tear the runtime down before the first frame.
    exit_code = asyncio.run(run_game())
    if sys.platform != "emscripten":
        sys.exit(exit_code)
