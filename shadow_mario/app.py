"""Canonical runtime entrypoint for the game."""

from __future__ import annotations

import asyncio
import sys

import pygame

from .app_context import build_app_context
from .scene_payloads import LevelStartPayload
from .scenes import (
    GameOverScene,
    GameScene,
    LevelSelectScene,
    LoadingScene,
    MenuScene,
    PauseScene,
    SceneManager,
    SettingsScene,
)


async def run_game() -> int:
    """Run the game loop and return process exit code."""
    pygame.init()
    context = build_app_context()
    config = context.config

    screen = pygame.display.set_mode((config.window_width, config.window_height))
    pygame.display.set_caption(config.title)
    clock = pygame.time.Clock()

    manager = SceneManager(screen, context)
    manager.register("menu", MenuScene)
    manager.register("game", GameScene)
    manager.register("pause", PauseScene)
    manager.register("game_over", GameOverScene)
    manager.register("settings", SettingsScene)
    manager.register("level_select", LevelSelectScene)
    manager.register("loading", LoadingScene)

    manager.replace("menu", LevelStartPayload(level=1))
    manager.apply_pending()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        if manager.is_empty():
            break

        manager.handle_events(events)
        manager.update(dt)

        current = manager.current_scene()
        if current is not None and current.is_done():
            next_name = current.get_next_scene_name()
            if next_name == "quit":
                running = False
            elif next_name:
                manager.replace(next_name, current.get_transition_data())

        manager.apply_pending()
        manager.draw()
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()
    return 0


def run() -> int:
    """Sync wrapper used by module and script entrypoints."""
    return asyncio.run(run_game())


def main() -> None:
    """CLI entrypoint."""
    raise SystemExit(run())


if __name__ == "__main__":
    sys.exit(run())
