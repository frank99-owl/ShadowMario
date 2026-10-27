"""Local playtest telemetry: one JSON line per gameplay event.

Nothing leaves the machine. Events go to `telemetry/events.jsonl` under the
project root (override with SHADOW_MARIO_TELEMETRY_DIR, disable with
SHADOW_MARIO_TELEMETRY=0). `tools/playtest_report.py` turns the file into
completion rates and a death heatmap per level.
"""

from __future__ import annotations

import json
import os
import time
import uuid


class Telemetry:
    """Append-only event log. A failed write is dropped, never raised."""

    def __init__(self, directory: str | None, enabled: bool = True) -> None:
        self.enabled = enabled and directory is not None
        self.path = os.path.join(directory, "events.jsonl") if directory else None
        # One id per game launch, so a report can tell a retry from a new player.
        self.session_id = uuid.uuid4().hex[:12]
        self._attempt = 0

    def _write(self, record: dict) -> None:
        if not self.enabled or self.path is None:
            return
        record = {"t": round(time.time(), 3), "session": self.session_id, **record}
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, separators=(",", ":")) + "\n")
        except OSError:
            self.enabled = False

    def level_start(self, level: int, seed: int) -> None:
        self._attempt += 1
        self._write({"kind": "level_start", "level": level, "attempt": self._attempt, "seed": seed})

    def gameplay_event(self, level: int, event: dict) -> None:
        self._write({"level": level, "attempt": self._attempt, **event})

    def level_end(self, level: int, outcome: str, **data) -> None:
        self._write({"kind": "level_end", "level": level, "attempt": self._attempt,
                     "outcome": outcome, **data})


_instance: Telemetry | None = None


def get_telemetry() -> Telemetry:
    global _instance
    if _instance is None:
        enabled = os.environ.get("SHADOW_MARIO_TELEMETRY", "1") != "0"
        directory = os.environ.get("SHADOW_MARIO_TELEMETRY_DIR")
        if directory is None:
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            directory = os.path.join(root, "telemetry")
        _instance = Telemetry(directory, enabled=enabled)
    return _instance
