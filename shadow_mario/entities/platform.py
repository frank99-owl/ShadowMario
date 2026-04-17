import pygame
from .moveable_entity import MoveableEntity


class Platform(MoveableEntity):
    """普通平台，玩家可以站在上面。"""

    RIGHT_BOUND = 3000

    def __init__(self, x, y, config, image_path=None, speed=None):
        img = image_path or config.platform_image
        spd = speed if speed is not None else config.platform_speed
        super().__init__(x, y, img, spd)

    def can_move_right(self):
        return self.x < self.RIGHT_BOUND

    def update(self, keys):
        if keys[pygame.K_RIGHT]:
            self.x -= self.scroll_speed
        elif keys[pygame.K_LEFT]:
            if self.can_move_right():
                self.x += self.scroll_speed
