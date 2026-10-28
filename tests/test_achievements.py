"""Achievements unlock for what they say, and only for that.

Three bugs, all live on the itch.io build until 2026-10-28:
- "Collect 50 coins in total" unlocked on a first run with 25: the game-over
  screen added the level's coins to the save, and the check added them again.
- "Complete Level 1 in under 60 seconds" was defined but never checked.
- "Complete a level without taking damage" compared health against 1.0, but
  the race counts health from 100, so any race win counted.

The scene tests pass plain dicts, as the scene manager does, so they also run
against the code from before these fixes and fail there.
"""

import pytest

from shadow_mario import achievements as achievements_module
from shadow_mario import save as save_module
from shadow_mario.achievements import AchievementManager
from shadow_mario.app_context import AppContext
from shadow_mario.audio import get_audio_manager
from shadow_mario.config import GameConfig
from shadow_mario.level import Level
from shadow_mario.runtime_config import get_runtime_config
from shadow_mario.save import SaveManager
from shadow_mario.scene_payloads import GameOverPayload
from shadow_mario.storage import FileStore


@pytest.fixture
def manager(tmp_path):
    return AchievementManager(SaveManager(FileStore(tmp_path)))


def test_coin_collector_needs_fifty_coins_in_the_save(manager):
    save = manager.save
    save.add_coins(27)
    assert "coin_collector" not in manager.check_level_complete(
        1, 27, 0.85, max_health=1.0, elapsed_time=90.0)
    save.add_coins(23)
    assert "coin_collector" in manager.check_level_complete(
        2, 23, 0.9, max_health=1.0, elapsed_time=90.0)


@pytest.mark.parametrize("level, seconds, unlocks", [
    (1, 13.3, True), (1, 59.9, True), (1, 60.0, False), (1, 0.0, False), (2, 13.3, False),
])
def test_speed_runner_is_level_1_under_60_seconds(manager, level, seconds, unlocks):
    unlocked = manager.check_level_complete(level, 10, 0.5, max_health=1.0, elapsed_time=seconds)
    assert ("speed_run" in unlocked) is unlocks


@pytest.mark.parametrize("health, max_health, unlocks", [
    (1.0, 1.0, True), (0.95, 1.0, False), (100.0, 100.0, True), (50.0, 100.0, False), (1.0, 100.0, False),
])
def test_untouchable_means_still_at_the_levels_full_health(manager, health, max_health, unlocks):
    unlocked = manager.check_level_complete(4, 10, health, max_health=max_health, elapsed_time=90.0)
    assert ("no_damage" in unlocked) is unlocks


def test_levels_report_their_starting_health():
    config = GameConfig()
    assert Level(config.level1_file, config, 1, seed=1).build_result().max_health == config.player_health
    race = Level(config.level4_file, config, 4, seed=1)
    assert race.player.health == race.build_result().max_health == Level.RACE_START_HEALTH


def test_payload_without_max_health_keeps_the_old_meaning():
    assert GameOverPayload.from_mapping({"won": True, "level": 2}).max_health == 1.0


@pytest.fixture
def fresh_game(tmp_path, monkeypatch):
    """An app context whose save, and the achievement manager's, start empty."""
    save = SaveManager(FileStore(tmp_path))
    monkeypatch.setattr(save_module, "_instance", save)
    monkeypatch.setattr(achievements_module, "_instance", None, raising=False)
    context = AppContext(config=GameConfig(), save=save, audio=get_audio_manager(),
                         runtime_config=get_runtime_config())
    return context, save


def _finish(context, **payload) -> list[str]:
    from shadow_mario.scenes import GameOverScene

    scene = GameOverScene(context)
    scene.on_enter({"won": True, "total_coins": 33, **payload})
    return scene._new_achievements


def test_first_run_with_27_coins_does_not_unlock_coin_collector(fresh_game):
    context, save = fresh_game
    unlocked = _finish(context, level=1, score=27, health=0.85, elapsed_time=13.3,
                       collected_coins=27, max_health=1.0)
    assert save.get_total_coins() == 27
    assert "first_blood" in unlocked and "coin_collector" not in unlocked
    assert "coin_collector" in _finish(context, level=2, score=23, health=0.85,
                                       elapsed_time=40.0, collected_coins=23, max_health=1.0)


def test_level_1_in_13_seconds_unlocks_speed_runner(fresh_game):
    context, _ = fresh_game
    assert "speed_run" in _finish(context, level=1, score=20, health=0.85, elapsed_time=13.3,
                                  collected_coins=20, max_health=1.0)


def test_winning_the_race_after_two_hits_is_not_untouchable(fresh_game):
    context, save = fresh_game
    # The level 4 reference replay: player 1 wins with 50 of 100 health.
    unlocked = _finish(context, level=4, score=58, health=50.0, elapsed_time=26.6,
                       collected_coins=30, p1_score=58, p2_score=0, race_winner=1, max_health=100.0)
    assert "no_damage" not in unlocked and not save.has_achievement("no_damage")
    assert "no_damage" in _finish(context, level=4, score=58, health=100.0, elapsed_time=26.6,
                                  collected_coins=30, p1_score=58, p2_score=0, race_winner=1,
                                  max_health=100.0)
