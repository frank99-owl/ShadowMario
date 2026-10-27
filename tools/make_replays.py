"""Generate the reference replays that CI plays back (tests/replays/).

A scripted player holds forward, jumps when an enemy or a boss fireball is
close, and fires once the boss is in range. It only changes its input on even
ticks, so each replay also plays back identically when the game samples input
at 30 fps (two ticks per frame). The recorded outcome becomes the expectation
`tests/test_replays.py` checks.

Run after an intentional change to the simulation:

    python tools/make_replays.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SHADOW_MARIO_TELEMETRY", "0")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from shadow_mario.config import GameConfig  # noqa: E402
from shadow_mario.input import InputFrame  # noqa: E402
from shadow_mario.level import Level  # noqa: E402
from shadow_mario.simulation import LevelRunner, Replay  # noqa: E402

REPLAY_DIR = ROOT / "tests" / "replays"
SEED = 20260427
MAX_TICKS = 60 * 120
JUMP_HOLD_TICKS = 20


def level_file(config: GameConfig, number: int) -> str:
    return {1: config.level1_file, 2: config.level2_file,
            3: config.level3_file, 4: config.level4_file}[number]


def build_level(number: int, seed: int) -> Level:
    config = GameConfig()
    return Level(level_file(config, number), config, number, seed=seed)


class ScriptedPlayer:
    """Deterministic policy over the level state; decides every other tick."""

    def __init__(self, level: Level) -> None:
        self.level = level
        race = level.camera_mode
        self.forward = pygame.K_d if race else pygame.K_RIGHT
        self.jump = pygame.K_w if race else pygame.K_UP
        self._jump_left = 0
        self._fire_toggle = False
        self._frame = InputFrame.of(self.forward)

    def _threat_ahead(self) -> bool:
        p = self.level.player
        for e in self.level.enemies:
            dx = e.x - p.x
            if 20 < dx < 115 and abs(e.y - p.y) < 60:
                return True
        for fb in self.level.fireballs:
            if fb.is_shot_by_player():
                continue
            dx = fb.x - p.x
            if abs(fb.y - p.y) < 60 and -10 < dx * -fb.direction < 140:
                return True
        return False

    def decide(self, tick: int) -> InputFrame:
        if tick % 2:
            return self._frame
        level, p = self.level, self.level.player
        keys = [self.forward]

        if self._jump_left > 0:
            self._jump_left -= 2
            keys.append(self.jump)
        elif not p.is_jumping and self._threat_ahead() and self._frame[self.jump] is False:
            self._jump_left = JUMP_HOLD_TICKS
            keys.append(self.jump)

        boss = level.boss
        if boss is not None and boss.health > 0 and abs(p.x - boss.x) < level.config.boss_activation_radius:
            # Fire on alternate decisions so every shot is a fresh S press.
            self._fire_toggle = not self._fire_toggle
            if self._fire_toggle:
                keys.append(pygame.K_s)

        self._frame = InputFrame.of(*keys)
        return self._frame


def record(number: int, seed: int = SEED) -> tuple[Replay, Level, LevelRunner]:
    level = build_level(number, seed)
    runner = LevelRunner(level, seed)
    policy = ScriptedPlayer(level)
    while not runner.is_finished() and runner.tick < MAX_TICKS:
        runner.step(policy.decide(runner.tick))
    return runner.replay, level, runner


def fingerprint(level: Level, runner: LevelRunner) -> dict:
    return {
        "outcome": "win" if level.is_win else ("loss" if level.is_loss else "timeout"),
        "ticks": runner.tick,
        "score": level.player.score,
        "health": round(level.player.health, 4),
        "hits": level.player_hits,
    }


def main() -> int:
    pygame.init()
    pygame.display.set_mode((1, 1))
    failed = False
    for number in (1, 2, 3, 4):
        replay, level, runner = record(number)
        result = fingerprint(level, runner)
        replay.note = "scripted reference run; regenerate with tools/make_replays.py"
        data = replay.to_dict()
        data["expect"] = result
        path = REPLAY_DIR / f"level{number}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        import json
        path.write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
        print(f"level {number}: {result}  -> {path.relative_to(ROOT)}")
        failed |= result["outcome"] != "win"
    pygame.quit()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
