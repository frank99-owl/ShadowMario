import pygame
from .game_entity import GameEntity


class MoveableEntity(GameEntity):
    """可随背景滚动的实体基类。"""

    def __init__(self, x, y, image_path, scroll_speed):
        super().__init__(x, y, image_path)
        self.scroll_speed = scroll_speed

    def update(self, keys):
        if keys[pygame.K_RIGHT]:
            self.x -= self.scroll_speed
        elif keys[pygame.K_LEFT]:
            self.x += self.scroll_speed
