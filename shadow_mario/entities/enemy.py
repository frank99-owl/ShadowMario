import random
import pygame
from .moveable_entity import MoveableEntity


class Enemy(MoveableEntity):
    """普通敌人，在范围内巡逻，只能伤害玩家一次。"""

    def __init__(self, x, y, config):
        super().__init__(x, y, config.enemy_image, config.enemy_speed)
        self.random_speed = config.enemy_random_speed
        self.max_displacement = config.enemy_max_displacement
        self.current_displacement = 0
        self.direction = 1 if random.choice([True, False]) else -1
        self.has_inflicted_damage = False

    def update(self, keys):
        super().update(keys)

        move_amount = self.direction * self.random_speed
        self.x += move_amount
        self.current_displacement += move_amount

        if abs(self.current_displacement) >= self.max_displacement:
            self.direction *= -1
            if self.current_displacement > self.max_displacement:
                self.current_displacement = self.max_displacement
            elif self.current_displacement < -self.max_displacement:
                self.current_displacement = -self.max_displacement

    def can_inflict_damage(self):
        return not self.has_inflicted_damage

    def set_has_inflicted_damage(self, value):
        self.has_inflicted_damage = value
