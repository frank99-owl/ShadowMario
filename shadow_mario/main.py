import sys
import os

import pygame
from shadow_mario.config import GameConfig
from shadow_mario.level import Level

# Game states
START_SCREEN = 0
LEVEL_1 = 1
LEVEL_2 = 2
LEVEL_3 = 3
END_SCREEN = 4


def main():
    pygame.init()

    # First create temp window to get size, then initialize config
    screen = pygame.display.set_mode((1024, 768))
    config = GameConfig()
    pygame.display.set_caption(config.title)
    pygame.display.set_mode((config.window_width, config.window_height))
    clock = pygame.time.Clock()

    # Load resources
    background_image = pygame.image.load(config.background_image).convert()

    current_state = START_SCREEN
    current_level = None

    # Key state tracking (simulate wasPressed)
    s_pressed_last_frame = False

    running = True
    while running:
        keys = pygame.key.get_pressed()
        s_just_pressed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if current_state == START_SCREEN:
                    if event.key == pygame.K_1:
                        current_level = Level(config.level1_file, config, 1)
                        current_state = LEVEL_1
                    elif event.key == pygame.K_2:
                        current_level = Level(config.level2_file, config, 2)
                        current_state = LEVEL_2
                    elif event.key == pygame.K_3:
                        current_level = Level(config.level3_file, config, 3)
                        current_state = LEVEL_3
                elif current_state == END_SCREEN:
                    if event.key == pygame.K_SPACE:
                        current_state = START_SCREEN
                        current_level = None

        # Detect S key wasPressed
        if keys[pygame.K_s] and not s_pressed_last_frame:
            s_just_pressed = True
        s_pressed_last_frame = keys[pygame.K_s]

        # Draw background
        screen.blit(background_image, (0, 0))

        if current_state == START_SCREEN:
            _draw_start_screen(screen, config)
        elif current_state == END_SCREEN:
            _draw_end_screen(screen, config, current_level)
        else:
            if current_level is not None:
                current_level.update(keys, s_just_pressed, screen)
                if current_level.is_win or current_level.is_loss:
                    current_state = END_SCREEN

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


def _draw_start_screen(screen, config):
    title_surf = config.title_font.render(config.msg_props.get("title", "SHADOW MARIO"), True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(config.window_width // 2, int(config.title_y)))
    screen.blit(title_surf, title_rect)

    instructions = config.msg_props.get("instruction", "USE ARROW KEYS TO MOVE\nENTER LEVEL TO START - 1, 2, 3")
    lines = instructions.split("\\n")
    start_y = int(config.message_y)
    for i, line in enumerate(lines):
        surf = config.instruction_font.render(line, True, (255, 255, 255))
        rect = surf.get_rect(center=(config.window_width // 2, start_y + i * 30))
        screen.blit(surf, rect)


def _draw_end_screen(screen, config, level):
    if level.is_win:
        msg = config.msg_props.get("gameWon", "Congratulations, You Won!\nPress Space to Continue")
    else:
        msg = config.msg_props.get("gameOver", "Game Over, You Lost!\nPress Space to Continue")
    msg = msg.upper()
    lines = msg.split("\\n")
    start_y = int(config.message_y)
    for i, line in enumerate(lines):
        surf = config.instruction_font.render(line, True, (255, 255, 255))
        rect = surf.get_rect(center=(config.window_width // 2, start_y + i * 30))
        screen.blit(surf, rect)


if __name__ == "__main__":
    main()
