"""Telemetry log and the playtest report built from it."""

import importlib.util
import json
from pathlib import Path

from shadow_mario.telemetry import Telemetry

ROOT = Path(__file__).resolve().parent.parent


def _report_module():
    spec = importlib.util.spec_from_file_location("playtest_report", ROOT / "tools" / "playtest_report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _two_attempts(directory: Path) -> Path:
    t = Telemetry(str(directory))
    t.level_start(1, seed=5)
    t.gameplay_event(1, {"kind": "damage", "tick": 90, "player": 1, "x": 430.0, "y": 668.0})
    t.gameplay_event(1, {"kind": "death", "tick": 400, "player": 1, "x": 1900.0, "y": 680.0})
    t.level_end(1, outcome="loss", tick=480, x=1900.0)
    t.level_start(1, seed=6)
    t.level_end(1, outcome="win", tick=840, x=4100.0)
    return directory / "events.jsonl"


def test_events_are_json_lines_tagged_by_session_and_attempt(tmp_path):
    path = _two_attempts(tmp_path)
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [r["kind"] for r in records] == ["level_start", "damage", "death", "level_end",
                                           "level_start", "level_end"]
    assert len({r["session"] for r in records}) == 1
    assert [r["attempt"] for r in records] == [1, 1, 1, 1, 2, 2]


def test_disabled_or_unwritable_telemetry_never_raises(tmp_path):
    Telemetry(str(tmp_path), enabled=False).level_start(1, seed=1)
    assert not (tmp_path / "events.jsonl").exists()
    blocker = tmp_path / "file"
    blocker.write_text("x")
    broken = Telemetry(str(blocker / "sub"))
    broken.level_start(1, seed=1)
    assert broken.enabled is False


def test_report_counts_first_try_clears_and_draws_heatmaps(tmp_path):
    report = _report_module()
    path = _two_attempts(tmp_path)
    by_level = report.group_attempts(report.load_events(path))
    table = report.summarise(by_level)
    row = next(line for line in table.splitlines() if line.startswith("| 1 |"))
    cells = [c.strip() for c in row.strip("|").split("|")]
    # attempts, players, won, lost, quit, first-try clear, s to first hit, s to clear
    assert cells[1:] == ["2", "1", "1", "1", "0", "0/1", "1.5", "14.0"]

    out = tmp_path / "report"
    assert report.main([str(path), "--out", str(out)]) == 0
    assert (out / "summary.md").exists()
    assert (out / "heatmap_level1.png").stat().st_size > 0
