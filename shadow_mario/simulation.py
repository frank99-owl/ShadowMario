"""Fixed-timestep driver and input replay for the level simulation.

The level rules are written per tick (speeds are pixels per tick, timers count
ticks), so the game only behaves the same everywhere if it advances a fixed
number of ticks per second of real time, whatever the display refresh rate.
`FixedStepClock` turns variable frame times into whole ticks; `LevelRunner`
feeds one `InputFrame` per tick into a `Level` and keeps the run-length encoded
input history, which `Replay` saves and loads.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import pygame

from .input import InputFrame

TICK_RATE = 60
TICK_DT = 1.0 / TICK_RATE
# Cap on ticks per rendered frame. A long stall (tab in background, debugger)
# drops time instead of fast-forwarding through it.
MAX_TICKS_PER_FRAME = 5
REPLAY_VERSION = 1


class FixedStepClock:
    """Accumulate frame time and release it as whole simulation ticks."""

    def __init__(self, tick_dt: float = TICK_DT, max_ticks: int = MAX_TICKS_PER_FRAME) -> None:
        self.tick_dt = tick_dt
        self.max_ticks = max_ticks
        self._accumulator = 0.0

    def advance(self, dt: float) -> int:
        self._accumulator += max(0.0, dt)
        # The epsilon keeps 60 frames of 1/60 s from rounding down to 59 ticks.
        ticks = int((self._accumulator + 1e-9) / self.tick_dt)
        if ticks > self.max_ticks:
            self._accumulator = 0.0
            return self.max_ticks
        self._accumulator -= ticks * self.tick_dt
        return ticks

    def reset(self) -> None:
        self._accumulator = 0.0


@dataclass
class Replay:
    """Recorded per-tick input for one level attempt."""

    level: int
    seed: int
    runs: list[list[int]] = field(default_factory=list)  # [[mask, tick_count], ...]
    note: str = ""

    def append(self, frame: InputFrame) -> None:
        if self.runs and self.runs[-1][0] == frame.mask:
            self.runs[-1][1] += 1
        else:
            self.runs.append([frame.mask, 1])

    def frames(self) -> Iterator[InputFrame]:
        for mask, count in self.runs:
            frame = InputFrame(mask)
            for _ in range(count):
                yield frame

    @property
    def tick_count(self) -> int:
        return sum(count for _, count in self.runs)

    def to_dict(self) -> dict:
        return {
            "version": REPLAY_VERSION,
            "level": self.level,
            "seed": self.seed,
            "note": self.note,
            "runs": self.runs,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Replay":
        if data.get("version") != REPLAY_VERSION:
            raise ValueError(f"unsupported replay version: {data.get('version')}")
        return cls(
            level=int(data["level"]),
            seed=int(data["seed"]),
            runs=[[int(m), int(c)] for m, c in data["runs"]],
            note=str(data.get("note", "")),
        )

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), separators=(",", ":")) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Replay":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


class LevelRunner:
    """Advance a Level one tick at a time and record the input it received."""

    def __init__(self, level, seed: int) -> None:
        self.level = level
        self.tick = 0
        self.replay = Replay(level=level.level_number, seed=seed)
        self._previous = InputFrame()

    def is_finished(self) -> bool:
        return self.level.is_win or self.level.is_loss

    def step(self, frame: InputFrame) -> None:
        s_just_pressed = frame[pygame.K_s] and not self._previous[pygame.K_s]
        self.level.update(frame, s_just_pressed)
        self.replay.append(frame)
        self._previous = frame
        self.tick += 1


def run_replay(level, replay: Replay, tail_ticks: int = 0) -> LevelRunner:
    """Play a replay into a freshly built level until it ends or input runs out.

    `tail_ticks` keeps stepping with no keys held afterwards, so a run whose
    final input lands mid-air still resolves.
    """
    runner = LevelRunner(level, replay.seed)
    for frame in replay.frames():
        if runner.is_finished():
            return runner
        runner.step(frame)
    idle = InputFrame()
    for _ in range(tail_ticks):
        if runner.is_finished():
            break
        runner.step(idle)
    return runner
