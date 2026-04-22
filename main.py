import asyncio
import sys

import pygame

from shadow_mario.config import GameConfig
from shadow_mario.scenes import (
    SceneManager,
    MenuScene,
    GameScene,
    PauseScene,
    GameOverScene,
    SettingsScene,
    LoadingScene,
)
from shadow_mario.scenes.level_select_scene import LevelSelectScene


async def main():
    pygame.init()
    config = GameConfig()

    screen = pygame.display.set_mode((config.window_width, config.window_height))
    pygame.display.set_caption(config.title)
    clock = pygame.time.Clock()

    # Scene manager
    manager = SceneManager(screen)
    manager.register("menu", MenuScene)
    manager.register("game", GameScene)
    manager.register("pause", PauseScene)
    manager.register("game_over", GameOverScene)
    manager.register("settings", SettingsScene)
    manager.register("level_select", LevelSelectScene)
    manager.register("loading", LoadingScene)

    # Initial scene
    manager.replace("menu")
    manager._apply_pending()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # seconds

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        if not manager._stack:
            break

        # Handle events
        manager.handle_events(events)

        # Update scene
        manager.update(dt)

        # Check scene transition requests
        if manager._stack:
            current = manager._stack[-1]
            if current.is_done():
                next_name = current.get_next_scene_name()

                if next_name == "quit":
                    running = False
                    continue
                else:
                    data = current.get_transition_data()
                    manager.replace(next_name, data)

        # Apply pending transitions
        manager._apply_pending()

        # Draw
        manager.draw()
        pygame.display.flip()

        # pygbag requires yielding control every frame
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()


asyncio.run(main())
