"""Tests for Level public APIs and behavior regressions."""

from pathlib import Path

from shadow_mario.config import GameConfig
from shadow_mario.level import Level


def _write_level_csv(path: Path, rows: list[str]) -> str:
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return str(path)


def test_level_snapshot_and_result_contract(tmp_path):
    config = GameConfig()
    level = Level(config.level1_file, config, level_number=1)

    snapshot = level.snapshot()
    result = level.build_result()

    assert snapshot.level_number == 1
    assert snapshot.total_coins >= snapshot.collected_coins
    assert result.level == 1
    assert isinstance(result.elapsed_time, float)


def test_trim_entities_right_of_end_flag(tmp_path):
    csv_path = _write_level_csv(
        tmp_path / "trim_level.csv",
        [
            "PLAYER,10,10",
            "END_FLAG,100,10",
            "PLATFORM,110,20",
            "COIN,120,20",
            "ENEMY,130,20",
            "DOUBLE_SCORE,140,20",
            "ENEMY_BOSS,150,20",
        ],
    )
    config = GameConfig()
    level = Level(csv_path, config, level_number=1)

    assert all(p.x <= 100 for p in level.platforms)
    assert all(c.x <= 100 for c in level.coins)
    assert all(e.x <= 100 for e in level.enemies)
    assert all(pu.x <= 100 for pu in level.power_ups)
    assert level.boss is None


def test_race_winner_flow(tmp_path):
    csv_path = _write_level_csv(
        tmp_path / "race_level.csv",
        [
            "PLAYER,10,10",
            "PLAYER,20,10",
            "END_FLAG,200,10",
        ],
    )
    config = GameConfig()
    level = Level(csv_path, config, level_number=4)

    level.player.score = 8
    level.player2.score = 3
    level.finalize_race_by_score()
    assert level.race_winner == 1
    assert level.is_win is True

    level2 = Level(csv_path, config, level_number=4)
    level2.force_race_winner(2)
    assert level2.race_winner == 2
    assert level2.is_win is True
