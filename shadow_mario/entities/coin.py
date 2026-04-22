import math

import pygame

from shadow_mario.config import GameConfig
from .moveable_entity import MoveableEntity


class Coin(MoveableEntity):
    """Coin entity, flies upward after being collected, with spinning animation.
    Respawns at original position after a delay."""

    FLY_SPEED = -10.0
    RESPAWN_DELAY = 3.0

    def __init__(self, x: float, y: float, config: GameConfig, allow_respawn: bool = True) -> None:
        super().__init__(x, y, config.coin_image, config.coin_speed, hitbox_scale=0.7)
        self._allow_respawn = allow_respawn
        self._is_collected = False
        self._original_x = x
        self._original_y = y
        self._respawn_timer = 0.0
        self.vertical_speed = 0.0
        self._spin_time = 0.0
        # Random starting phase so coins don't spin in sync
        self._spin_phase = x * 0.05

    def update(self, keys) -> None:
        if not self._is_collected:
            super().update(keys)
            self._spin_time += 1 / 60
        else:
            self.y += self.vertical_speed
            self._spin_time += 1 / 60
            if self.y < 0:
                self.active = False

            if self._allow_respawn:
                # Countdown to respawn
                self._respawn_timer -= 1 / 60
                if self._respawn_timer <= 0:
                    self._respawn()

    def update_spin_only(self) -> None:
        """Update spin animation and collected-coin flight (for camera mode)."""
        self._spin_time += 1 / 60
        if self._is_collected:
            self.y += self.vertical_speed
            if self.y < 0:
                self.active = False
            if self._allow_respawn:
                self._respawn_timer -= 1 / 60
                if self._respawn_timer <= 0:
                    self._respawn()

    def _respawn(self) -> None:
        """Respawn coin at original position."""
        self._is_collected = False
        self.active = True
        self.x = self._original_x
        self.y = self._original_y
        self.vertical_speed = 0.0

    def draw(self, screen: pygame.Surface, offset: tuple[float, float] = (0, 0)) -> None:
        if not self.active:
            return

        # Spin animation: scale width to simulate 3D rotation
        spin = math.sin(self._spin_time * 4 + self._spin_phase)
        scale_x = 0.6 + 0.4 * abs(spin)  # Scale between 0.6 and 1.0

        # Scale the image
        orig_rect = self.image.get_rect()
        new_width = int(orig_rect.width * scale_x)
        if new_width < 1:
            new_width = 1
        scaled = pygame.transform.scale(self.image, (new_width, orig_rect.height))

        # Position centered with offset
        draw_x = int(self.x + offset[0])
        draw_y = int(self.y + offset[1])
        rect = scaled.get_rect(center=(draw_x, draw_y))
        screen.blit(scaled, rect)

        # Shine effect when facing camera (spin near 1)
        if spin > 0.8:
            shine = pygame.Surface((new_width, orig_rect.height), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 60))
            screen.blit(shine, rect)

    def collect(self) -> None:
        if not self._is_collected:
            self._is_collected = True
            self.vertical_speed = self.FLY_SPEED
            if self._allow_respawn:
                self._respawn_timer = self.RESPAWN_DELAY

    def is_collected(self) -> bool:
        return self._is_collected

    def can_collect(self) -> bool:
        return not self._is_collected and self.active
