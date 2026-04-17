import random
import pygame
from .platform import Platform


class FlyingPlatform(Platform):
    """飞行平台，会随机水平移动。"""

    def __init__(self, x, y, config):
        super().__init__(x, y, config, config.flying_platform_image, config.flying_platform_speed)
        self.random_speed = config.flying_platform_random_speed
        self.max_displacement = config.flying_platform_max_displacement
        self.current_displacement = 0
        self.direction = 1 if random.choice([True, False]) else -1
        self.last_random_move = 0

    def can_move_right(self):
        return True

    def update(self, keys):
        # 先执行背景滚动
        super().update(keys)

        # 随机水平移动
        move_amount = self.direction * self.random_speed
        self.x += move_amount
        self.current_displacement += move_amount
        self.last_random_move = move_amount

        if abs(self.current_displacement) >= self.max_displacement:
            self.direction *= -1
            if self.current_displacement > self.max_displacement:
                self.current_displacement = self.max_displacement
            elif self.current_displacement < -self.max_displacement:
                self.current_displacement = -self.max_displacement
