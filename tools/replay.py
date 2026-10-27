"""Watch a recorded attempt: F9 during play saves one to replays/.

    python tools/replay.py replays/level1_20261027_190501.json
    python tools/replay.py tests/replays/level3.json --headless   # print the outcome only

Plays the input back through the real game scene at 60 ticks per second, so
camera, effects and tutorial hints look as they did live.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SHADOW_MARIO_TELEMETRY", "0")  # watching is not playing
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("replay")
    parser.add_argument("--headless", action="store_true", help="no window; print the outcome")
    args = parser.parse_args(argv)
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    import pygame

    from shadow_mario.app_context import build_app_context
    from shadow_mario.scenes import GameScene
    from shadow_mario.simulation import TICK_DT, Replay

    replay = Replay.load(args.replay)
    pygame.init()
    context = build_app_context()
    screen = pygame.display.set_mode((context.config.window_width, context.config.window_height))
    pygame.display.set_caption(f"Replay: level {replay.level}")
    clock = pygame.time.Clock()

    scene = GameScene(context)
    scene.on_enter({"level": replay.level})
    scene.play_replay(replay)

    # Input ends a few seconds after the last recorded tick at most.
    limit = replay.tick_count + 60 * 5
    while scene._runner.tick < limit:
        dt = TICK_DT if args.headless else clock.tick(60) / 1000.0
        if any(e.type == pygame.QUIT for e in pygame.event.get()):
            break
        scene.update(dt)
        if not args.headless:
            scene.draw(screen)
            pygame.display.flip()
        level = scene._level
        if level.is_win or level.is_loss:
            break

    level = scene._level
    outcome = "win" if level.is_win else ("loss" if level.is_loss else "unfinished")
    print(f"level {replay.level}: {outcome} after {scene._runner.tick} ticks, "
          f"score {level.player.score}, hits {level.player_hits}")
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
