"""One-off headless screenshot capture for README (not part of the game)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from shadow_mario.app_context import build_app_context  # noqa: E402
from shadow_mario.scene_payloads import LevelStartPayload  # noqa: E402
from shadow_mario.scenes import (  # noqa: E402
    GameOverScene,
    GameScene,
    LevelSelectScene,
    LoadingScene,
    MenuScene,
    PauseScene,
    SceneManager,
    SettingsScene,
)

pygame.init()
context = build_app_context()
config = context.config
screen = pygame.display.set_mode((config.window_width, config.window_height))

manager = SceneManager(screen, context)
for name, cls in [
    ("menu", MenuScene),
    ("game", GameScene),
    ("pause", PauseScene),
    ("game_over", GameOverScene),
    ("settings", SettingsScene),
    ("level_select", LevelSelectScene),
    ("loading", LoadingScene),
]:
    manager.register(name, cls)

os.makedirs("docs/screenshots", exist_ok=True)


def capture(scene: str, level: int, frames: int, out: str) -> None:
    manager.replace(scene, LevelStartPayload(level=level))
    manager.apply_pending()
    for _ in range(frames):
        manager.handle_events([])
        manager.update(1 / 60)
        manager.apply_pending()
        manager.draw()
    pygame.image.save(screen, out)
    print("saved", out, screen.get_size())


capture("menu", 1, 30, "docs/screenshots/menu.png")
capture("game", 1, 60, "docs/screenshots/level1.png")
capture("game", 3, 60, "docs/screenshots/level3-boss.png")
capture("game", 4, 60, "docs/screenshots/level4-race.png")
pygame.quit()
