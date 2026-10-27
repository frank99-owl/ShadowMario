"""Recorded-input regression tests: the same input must keep finishing each level.

A failure here means the simulation changed. If the change was intended,
regenerate the reference runs with `python tools/make_replays.py` and say why
in the commit; if not, the diff just broke how a level plays.
"""

import json
from pathlib import Path

import pygame
import pytest

from shadow_mario.config import GameConfig
from shadow_mario.input import InputFrame
from shadow_mario.level import Level
from shadow_mario.simulation import FixedStepClock, LevelRunner, Replay, run_replay

REPLAY_DIR = Path(__file__).parent / "replays"
LEVEL_FILES = {1: "level1_file", 2: "level2_file", 3: "level3_file", 4: "level4_file"}


def _level(number: int, seed: int) -> Level:
    config = GameConfig()
    return Level(getattr(config, LEVEL_FILES[number]), config, number, seed=seed)


def _load(number: int) -> tuple[Replay, dict]:
    data = json.loads((REPLAY_DIR / f"level{number}.json").read_text(encoding="utf-8"))
    return Replay.from_dict(data), data["expect"]


def _fingerprint(level: Level, ticks: int) -> dict:
    return {
        "outcome": "win" if level.is_win else ("loss" if level.is_loss else "timeout"),
        "ticks": ticks,
        "score": level.player.score,
        "health": round(level.player.health, 4),
        "hits": level.player_hits,
    }


@pytest.mark.parametrize("number", [1, 2, 3, 4])
def test_reference_replay_still_finishes_level(number):
    replay, expect = _load(number)
    level = _level(number, replay.seed)
    runner = run_replay(level, replay)
    assert _fingerprint(level, runner.tick) == expect


def _play_at_fps(number: int, fps: int) -> dict:
    """Drive the level the way GameScene does: input sampled once per rendered frame."""
    replay, _ = _load(number)
    timeline = list(replay.frames())
    level = _level(number, replay.seed)
    runner = LevelRunner(level, replay.seed)
    clock = FixedStepClock()
    frame_dt = 1.0 / fps
    frame_index = 0
    while not runner.is_finished() and runner.tick < len(timeline):
        frame_start = frame_index * frame_dt
        sample = timeline[min(len(timeline) - 1, int(frame_start * 60 + 1e-9))]
        for _ in range(clock.advance(frame_dt)):
            if runner.is_finished():
                break
            runner.step(sample)
        frame_index += 1
    return _fingerprint(level, runner.tick)


@pytest.mark.parametrize("number", [1, 3])
@pytest.mark.parametrize("fps", [30, 60, 144])
def test_outcome_does_not_depend_on_frame_rate(number, fps):
    _, expect = _load(number)
    assert _play_at_fps(number, fps) == expect


@pytest.mark.parametrize("fps", [24, 30, 60, 75, 144, 240])
def test_clock_releases_sixty_ticks_per_second(fps):
    clock = FixedStepClock()
    ticks = sum(clock.advance(1.0 / fps) for _ in range(fps * 10))
    assert ticks == 600


def test_clock_drops_time_after_a_stall():
    clock = FixedStepClock()
    assert clock.advance(2.0) == clock.max_ticks
    assert clock.advance(1.0 / 60) == 1


def test_replay_round_trip(tmp_path):
    replay = Replay(level=2, seed=7)
    for frame in [InputFrame.of(pygame.K_RIGHT)] * 3 + [InputFrame()] + [InputFrame.of(pygame.K_UP)] * 2:
        replay.append(frame)
    assert replay.runs == [[InputFrame.of(pygame.K_RIGHT).mask, 3], [0, 1], [InputFrame.of(pygame.K_UP).mask, 2]]
    path = tmp_path / "r.json"
    replay.save(path)
    loaded = Replay.load(path)
    assert loaded.runs == replay.runs and loaded.seed == 7 and loaded.tick_count == 6


def _write_csv(tmp_path, rows) -> str:
    path = tmp_path / "level.csv"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return str(path)


def _steps(level: Level, frame: InputFrame, ticks: int) -> LevelRunner:
    runner = LevelRunner(level, level.seed)
    for _ in range(ticks):
        runner.step(frame)
    return runner


def test_falling_onto_a_flying_platform_lands_at_any_height(tmp_path):
    # Under the spec's 1 px end-of-tick window, a jump from the ground could
    # only land on 37 of 300 platform heights; 560 was one of the misses.
    config = GameConfig()
    for platform_y in (530, 545, 560, 575):
        csv = _write_csv(tmp_path, ["PLATFORM,3000,745", "PLAYER,100,687",
                                    f"FLYING_PLATFORM,100,{platform_y}"])
        level = Level(csv, config, 2, seed=1)
        rest_y = platform_y - config.flying_platform_half_height
        _steps(level, InputFrame(), 5)  # settle on the ground
        _steps(level, InputFrame.of(pygame.K_UP), 22)
        _steps(level, InputFrame(), 40)
        assert level.player.y == pytest.approx(rest_y), platform_y
        assert level.player.is_jumping is False


def test_flying_platform_is_one_way_from_below(tmp_path):
    config = GameConfig()
    csv = _write_csv(tmp_path, ["PLATFORM,3000,745", "PLAYER,100,687", "FLYING_PLATFORM,100,600"])
    level = Level(csv, config, 2, seed=1)
    _steps(level, InputFrame(), 5)
    ys = []
    runner = LevelRunner(level, 1)
    for i in range(30):
        runner.step(InputFrame.of(pygame.K_UP) if i < 22 else InputFrame())
        ys.append(level.player.y)
    # The jump rises past the platform instead of snapping onto it on the way up.
    assert min(ys) < 600 - config.flying_platform_half_height - 50


def _ground_level(tmp_path) -> Level:
    csv = _write_csv(tmp_path, ["PLATFORM,3000,745", "PLAYER,100,687"])
    level = Level(csv, GameConfig(), 1, seed=1)
    _steps(level, InputFrame(), 5)
    return level


def _apex_rise(level: Level, hold_ticks: int) -> float:
    ground_y = level.player.y
    runner = LevelRunner(level, 1)
    lowest = ground_y
    for i in range(60):
        runner.step(InputFrame.of(pygame.K_UP) if i < hold_ticks else InputFrame())
        lowest = min(lowest, level.player.y)
    return ground_y - lowest


def test_tap_is_a_hop_and_hold_is_the_full_jump(tmp_path):
    hop = _apex_rise(_ground_level(tmp_path), hold_ticks=1)
    full = _apex_rise(_ground_level(tmp_path), hold_ticks=25)
    assert full == 210  # the original spec arc: -20 px/tick, +1 per tick
    assert 60 < hop < 90  # still clears an enemy (centres 42 px apart collide)


def test_jump_pressed_just_before_landing_is_buffered(tmp_path):
    level = _ground_level(tmp_path)
    runner = LevelRunner(level, 1)
    for _ in range(22):
        runner.step(InputFrame.of(pygame.K_UP))
    for _ in range(15):
        runner.step(InputFrame())
    assert level.player.is_jumping  # still descending
    # Press about 4 ticks before touchdown (the full arc lasts 41 ticks) and let go.
    jumps_before = level.player_jumps
    for i in range(10):
        runner.step(InputFrame.of(pygame.K_UP) if i < 1 else InputFrame())
    assert level.player_jumps == jumps_before + 1


def test_boss_hits_do_not_count_as_the_player_being_hurt():
    replay, expect = _load(3)
    level = _level(3, replay.seed)
    events = []
    runner = LevelRunner(level, replay.seed)
    for frame in replay.frames():
        if runner.is_finished():
            break
        runner.step(frame)
        events.extend(level.drain_events())
    assert level.boss is None or level.boss.health <= 0
    damage = [e for e in events if e["kind"] == "damage"]
    assert len(damage) == level.player_hits == expect["hits"]


def test_events_carry_level_coordinates():
    replay, _ = _load(1)
    level = _level(1, replay.seed)
    runner = LevelRunner(level, replay.seed)
    events = []
    for frame in replay.frames():
        if runner.is_finished():
            break
        runner.step(frame)
        events.extend(level.drain_events())
    assert events, "the reference run takes hits, so it should log them"
    enemy_xs = sorted(e.x for e in _level(1, replay.seed).enemies)
    for event in events:
        # A hit lands within an enemy's patrol range (+-50 px) plus contact distance.
        assert min(abs(event["x"] - x) for x in enemy_xs) < 50 + 42 + 5
    ticks = [e["tick"] for e in events]
    assert ticks == sorted(ticks)


def _always(level: Level, frame: InputFrame, max_ticks: int) -> LevelRunner:
    runner = LevelRunner(level, level.seed)
    while not runner.is_finished() and runner.tick < max_ticks:
        runner.step(frame)
    return runner


def _jump_across_flag(level: Level, run_key: int, jump_key: int, jump_at: int, ticks: int) -> None:
    """Run right and take one full jump starting at tick `jump_at`."""
    runner = LevelRunner(level, level.seed)
    while not runner.is_finished() and runner.tick < ticks:
        jumping = jump_at <= runner.tick < jump_at + 15
        runner.step(InputFrame.of(run_key, jump_key) if jumping else InputFrame.of(run_key))


def test_jumping_over_the_flag_still_ends_the_level(tmp_path):
    # The flag reaches the player after ~100 ticks; a full jump started at
    # tick 80 is near its apex then. The spec's radius test alone never
    # fires for this run, so the flag scrolled away and the level never ended.
    csv = _write_csv(tmp_path, ["PLATFORM,500,745", "PLAYER,100,687", "END_FLAG,600,670"])
    level = Level(csv, GameConfig(), 1, seed=1)
    _jump_across_flag(level, pygame.K_RIGHT, pygame.K_UP, jump_at=80, ticks=300)
    assert level.is_win


def test_passing_the_flag_with_the_boss_alive_does_not_win(tmp_path):
    csv = _write_csv(tmp_path, ["PLATFORM,500,745", "PLAYER,100,687",
                                "END_FLAG,600,670", "ENEMY_BOSS,590,680"])
    level = Level(csv, GameConfig(), 3, seed=1)
    level.player.invincibility_frames = 10_000  # keep the boss's fire out of it
    _always(level, InputFrame.of(pygame.K_RIGHT), 200)
    assert level.boss.health > 0
    assert not level.is_win
    level.boss.health = 0
    _always(level, InputFrame(), 5)
    assert level.is_win


def test_race_jumping_over_the_flag_finishes_the_race(tmp_path):
    csv = _write_csv(tmp_path, ["PLATFORM,400,745", "PLAYER,100,687", "PLAYER,100,687",
                                "END_FLAG,500,670"])
    level = Level(csv, GameConfig(), 4, seed=1)
    _jump_across_flag(level, pygame.K_d, pygame.K_w, jump_at=55, ticks=300)
    assert level.is_win and level.race_winner is not None
