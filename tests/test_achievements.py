"""Achievements count each coin once.

The game-over screen adds the level's coins to the save and then checks
achievements; the check used to add the level's coins a second time, so
"Collect 50 coins in total" unlocked on a first run with 25. Seen on the live
itch.io build on 2026-10-28: 27 coins, Coin Collector unlocked.
"""

import pytest

from shadow_mario import achievements as achievements_module
from shadow_mario import save as save_module
from shadow_mario.achievements import AchievementManager
from shadow_mario.app_context import AppContext
from shadow_mario.audio import get_audio_manager
from shadow_mario.config import GameConfig
from shadow_mario.runtime_config import get_runtime_config
from shadow_mario.save import SaveManager
from shadow_mario.scene_payloads import GameOverPayload
from shadow_mario.storage import FileStore


def test_coin_collector_needs_fifty_coins_in_the_save(tmp_path):
    save = SaveManager(FileStore(tmp_path))
    manager = AchievementManager(save)

    save.add_coins(27)
    assert "coin_collector" not in manager.check_level_complete(1, score=27, health=0.85)

    save.add_coins(23)
    assert "coin_collector" in manager.check_level_complete(2, score=23, health=0.9)
    assert save.has_achievement("coin_collector")


@pytest.fixture
def fresh_game(tmp_path, monkeypatch):
    """An app context whose save, and the achievement manager's, start empty."""
    save = SaveManager(FileStore(tmp_path))
    monkeypatch.setattr(save_module, "_instance", save)
    monkeypatch.setattr(achievements_module, "_instance", None, raising=False)
    context = AppContext(config=GameConfig(), save=save, audio=get_audio_manager(),
                         runtime_config=get_runtime_config())
    return context, save


def _finish_level(context, level: int, coins: int) -> list[str]:
    from shadow_mario.scenes import GameOverScene

    scene = GameOverScene(context)
    scene.on_enter(GameOverPayload(won=True, level=level, score=coins, health=0.85,
                                   elapsed_time=13.3, total_coins=33,
                                   collected_coins=coins).to_dict())
    return scene._new_achievements


def test_first_run_with_27_coins_does_not_unlock_coin_collector(fresh_game):
    context, save = fresh_game
    unlocked = _finish_level(context, level=1, coins=27)
    assert save.get_total_coins() == 27
    assert unlocked == ["first_blood"]
    assert not save.has_achievement("coin_collector")

    assert "coin_collector" in _finish_level(context, level=2, coins=23)  # 50 in total
