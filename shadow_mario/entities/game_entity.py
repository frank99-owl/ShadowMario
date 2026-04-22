"""Game entity base class."""

from typing import Optional

import pygame

from shadow_mario.runtime_config import get_runtime_config


class GameEntity:
    """Abstract base class for all game entities."""

    def __init__(self, x: float, y: float, image_path: str,
                 hitbox_scale: float | None = None) -> None:
        self._x = x
        self._y = y
        self.image = pygame.image.load(image_path).convert_alpha()
        self.active = True
        # If hitbox_scale is not specified, read default from RuntimeConfig
        if hitbox_scale is None:
            hitbox_scale = get_runtime_config().hitbox_scale("platform")
        self._hitbox_scale = hitbox_scale
        self._hitbox_offset_x = 0.0
        self._hitbox_offset_y = 0.0

    def draw(self, screen: pygame.Surface, offset: tuple[float, float] = (0, 0)) -> None:
        if self.active:
            rect = self.image.get_rect(center=(self._x + offset[0], self._y + offset[1]))
            screen.blit(self.image, rect)

    def update(self, keys) -> None:
        raise NotImplementedError

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        self._x = value

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        self._y = value

    def get_bounding_box(self) -> pygame.Rect:
        """Get the full image bounding box."""
        return self.image.get_rect(center=(self._x, self._y))

    def get_hitbox(self) -> pygame.Rect:
        """Get the scaled hitbox for collision detection (more precise collision)."""
        bbox = self.get_bounding_box()
        w = int(bbox.width * self._hitbox_scale)
        h = int(bbox.height * self._hitbox_scale)
        x = bbox.centerx - w // 2 + int(self._hitbox_offset_x)
        y = bbox.centery - h // 2 + int(self._hitbox_offset_y)
        return pygame.Rect(x, y, w, h)

    def set_hitbox_offset(self, offset_x: float, offset_y: float) -> None:
        """Set hitbox offset."""
        self._hitbox_offset_x = offset_x
        self._hitbox_offset_y = offset_y

    def collides_with(self, other: "GameEntity") -> bool:
        """Detect rectangular collision with another entity."""
        return self.get_hitbox().colliderect(other.get_hitbox())

    def get_collision_direction(self, other: "GameEntity") -> Optional[str]:
        """Get the collision direction (from other's perspective looking at self).

        Returns: "top", "bottom", "left", "right" or None
        """
        if not self.collides_with(other):
            return None

        self_rect = self.get_hitbox()
        other_rect = other.get_hitbox()

        # Calculate overlap in each direction
        overlap_top = self_rect.bottom - other_rect.top      # self collides from top
        overlap_bottom = other_rect.bottom - self_rect.top   # self collides from bottom
        overlap_left = self_rect.right - other_rect.left     # self collides from left
        overlap_right = other_rect.right - self_rect.left    # self collides from right

        # The direction with minimum overlap is the collision direction
        overlaps = {
            "top": overlap_top,
            "bottom": overlap_bottom,
            "left": overlap_left,
            "right": overlap_right,
        }
        return min(overlaps, key=overlaps.get)
