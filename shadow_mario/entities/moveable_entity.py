"""Moveable entity base class."""

import pygame

from .game_entity import GameEntity


class MoveableEntity(GameEntity):
    """Base class for entities that scroll with the background."""

    def __init__(self, x: float, y: float, image_path: str, scroll_speed: float,
                 hitbox_scale: float = 0.8) -> None:
        super().__init__(x, y, image_path, hitbox_scale)
        self.scroll_speed = scroll_speed

    def update(self, keys) -> None:
        if keys[pygame.K_RIGHT]:
            self.x -= self.scroll_speed
        elif keys[pygame.K_LEFT]:
            self.x += self.scroll_speed
