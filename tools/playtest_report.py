"""Summarise playtest telemetry and draw where players got hurt, per level.

    python tools/playtest_report.py                       # telemetry/events.jsonl
    python tools/playtest_report.py path/to/events.jsonl --out telemetry/report

Writes `summary.md` plus `heatmap_level<N>.png` into --out. Each heatmap is the
level's layout squashed to one strip, with every damage (orange), death (red)
and abandoned attempt (grey) marked at the level x where it happened.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

ROOT = Path(__file__).resolve().parent.parent
LEVEL_CSV = {n: ROOT / "res" / f"level{n}.csv" for n in (1, 2, 3, 4)}
TICK_RATE = 60


def load_events(path: Path) -> list[dict]:
    events = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def group_attempts(events: list[dict]) -> dict[int, list[dict]]:
    """level -> attempts, each {session, attempt, end, damage[], death[]}."""
    attempts: dict[tuple, dict] = {}
    for e in events:
        key = (e.get("session"), e.get("attempt"))
        level = e.get("level")
        if level is None:
            continue
        a = attempts.setdefault(key, {"session": key[0], "attempt": key[1], "level": level,
                                      "end": None, "damage": [], "death": []})
        kind = e.get("kind")
        if kind == "level_end":
            a["end"] = e
        elif kind in ("damage", "death"):
            a[kind].append(e)
    by_level: dict[int, list[dict]] = defaultdict(list)
    for a in attempts.values():
        by_level[a["level"]].append(a)
    for items in by_level.values():
        items.sort(key=lambda a: (a["session"] or "", a["attempt"] or 0))
    return by_level


def _median(values: list[float]) -> str:
    return f"{statistics.median(values):.1f}" if values else "-"


def summarise(by_level: dict[int, list[dict]]) -> str:
    lines = [
        "| Level | Attempts | Players | Won | Lost | Quit/restart | First-try clear | "
        "Median s to first hit | Median s to clear |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for level in sorted(by_level):
        items = by_level[level]
        outcomes = [(a["end"] or {}).get("outcome", "open") for a in items]
        sessions = {a["session"] for a in items}
        first_tries = {}
        for a in items:
            first_tries.setdefault(a["session"], a)
        first_clear = sum(1 for a in first_tries.values()
                          if (a["end"] or {}).get("outcome") == "win")
        first_hit = [a["damage"][0]["tick"] / TICK_RATE for a in items if a["damage"]]
        clear = [a["end"]["tick"] / TICK_RATE for a in items
                 if a["end"] and a["end"].get("outcome") == "win"]
        lines.append(
            f"| {level} | {len(items)} | {len(sessions)} | {outcomes.count('win')} | "
            f"{outcomes.count('loss')} | {outcomes.count('quit') + outcomes.count('restart')} | "
            f"{first_clear}/{len(first_tries)} | {_median(first_hit)} | {_median(clear)} |"
        )
    return "\n".join(lines)


def _layout(level: int) -> list[tuple[str, float, float]]:
    with LEVEL_CSV[level].open(encoding="utf-8") as fh:
        return [(row[0], float(row[1]), float(row[2])) for row in csv.reader(fh) if len(row) >= 3]


def draw_heatmap(level: int, attempts: list[dict], out_path: Path) -> None:
    import pygame

    pygame.init()
    layout = _layout(level)
    flag_x = max((x for kind, x, _ in layout if kind == "END_FLAG"), default=4000.0)
    world_w = flag_x + 200
    width, height = 1600, 260
    sx = width / world_w
    sy = height / 800

    surf = pygame.Surface((width, height))
    surf.fill((24, 26, 34))
    for kind, x, y in layout:
        px, py = int(x * sx), int(y * sy)
        if kind == "PLATFORM":
            pygame.draw.line(surf, (90, 90, 110), (0, int((y - 25) * sy)), (width, int((y - 25) * sy)), 2)
        elif kind == "FLYING_PLATFORM":
            pygame.draw.line(surf, (120, 120, 150), (int((x - 200) * sx), py), (int((x + 200) * sx), py), 3)
        elif kind == "ENEMY":
            pygame.draw.circle(surf, (170, 60, 60), (px, py), 3)
        elif kind == "ENEMY_BOSS":
            pygame.draw.circle(surf, (220, 40, 40), (px, py), 8, 2)
        elif kind == "COIN":
            pygame.draw.circle(surf, (200, 170, 40), (px, py), 2)
        elif kind == "END_FLAG":
            pygame.draw.line(surf, (120, 220, 120), (px, py - 30), (px, py + 20), 3)

    def mark(event_x: float, event_y: float, color, radius: int) -> None:
        dot = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot, (*color, 110), (radius, radius), radius)
        surf.blit(dot, (int(event_x * sx) - radius, int(event_y * sy) - radius))

    for a in attempts:
        for e in a["damage"]:
            mark(e["x"], e["y"], (255, 150, 40), 6)
        for e in a["death"]:
            mark(e["x"], e["y"], (255, 40, 40), 10)
        end = a["end"] or {}
        if end.get("outcome") in ("quit", "restart") and end.get("x") is not None:
            mark(end["x"], 120, (180, 180, 180), 7)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surf, str(out_path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("events", nargs="?", default=str(ROOT / "telemetry" / "events.jsonl"))
    parser.add_argument("--out", default=str(ROOT / "telemetry" / "report"))
    args = parser.parse_args(argv)

    path = Path(args.events)
    if not path.exists():
        print(f"no telemetry at {path}; play the game first", file=sys.stderr)
        return 1
    by_level = group_attempts(load_events(path))
    out = Path(args.out)
    table = summarise(by_level)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(
        "# Playtest summary\n\n" + table + "\n\n"
        "Heatmaps: orange = damage, red = death, grey = quit or restart.\n",
        encoding="utf-8",
    )
    for level, attempts in sorted(by_level.items()):
        if level in LEVEL_CSV:
            draw_heatmap(level, attempts, out / f"heatmap_level{level}.png")
    print(table)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
