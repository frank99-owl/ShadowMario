import pygame

from shadow_mario.config import GameConfig
from .moveable_entity import MoveableEntity


class Platform(MoveableEntity):
    """Normal platform, player can stand on it."""

    RIGHT_BOUND = 3000

    def __init__(self, x: float, y: float, config: GameConfig,
                 image_path: str | None = None, speed: float | None = None) -> None:
        img = image_path or config.platform_image
        spd = speed if speed is not None else config.platform_speed
        super().__init__(x, y, img, spd, hitbox_scale=1.0)

    def can_move_right(self) -> bool:
        return self.x < self.RIGHT_BOUND

    def update(self, keys) -> None:
        if keys[pygame.K_RIGHT]:
            self.x -= self.scroll_speed
        elif keys[pygame.K_LEFT]:
            if self.can_move_right():
                self.x += self.scroll_speed
