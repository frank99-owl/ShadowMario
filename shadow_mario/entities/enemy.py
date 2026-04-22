import random

import pygame

from shadow_mario.config import GameConfig
from .moveable_entity import MoveableEntity


class Enemy(MoveableEntity):
    """Normal enemy, patrols within range, can damage player with cooldown."""

    DAMAGE_COOLDOWN = 1.5  # Seconds between damage ticks
    PATROL_RANGE_COLOR = (255, 50, 50, 40)  # Semi-transparent red

    def __init__(self, x: float, y: float, config: GameConfig) -> None:
        super().__init__(x, y, config.enemy_image, config.enemy_speed, hitbox_scale=0.85)
        self.random_speed = config.enemy_random_speed
        self.max_displacement = config.enemy_max_displacement
        self.current_displacement = 0.0
        self.direction = 1 if random.choice([True, False]) else -1
        self.has_inflicted_damage = False
        self.damage_cooldown_timer = 0.0
        # Store spawn position for patrol range visualization
        self.spawn_x = x

    def update(self, keys) -> None:
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

        # Decrease damage cooldown
        if self.damage_cooldown_timer > 0:
            self.damage_cooldown_timer -= 1 / 60
            if self.damage_cooldown_timer <= 0:
                # Cooldown over, can damage again
                self.has_inflicted_damage = False

    def can_inflict_damage(self) -> bool:
        return not self.has_inflicted_damage and self.damage_cooldown_timer <= 0

    def set_has_inflicted_damage(self, value: bool) -> None:
        self.has_inflicted_damage = value
        if value:
            self.damage_cooldown_timer = self.DAMAGE_COOLDOWN

    def draw(self, screen: pygame.Surface, offset: tuple[float, float] = (0, 0)) -> None:
        super().draw(screen, offset)

        # Flash red briefly when on cooldown and could damage again soon
        if 0 < self.damage_cooldown_timer < 0.3:
            flash = pygame.Surface((32, 32), pygame.SRCALPHA)
            flash.fill((255, 0, 0, 100))
            rect = flash.get_rect(center=(int(self.x + offset[0]), int(self.y + offset[1])))
            screen.blit(flash, rect)
