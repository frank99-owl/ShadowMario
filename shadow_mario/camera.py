"""Camera system, responsible for smooth player following and screen shake effects."""

import random

import pygame


class Camera:
    """Game camera, smoothly follows target and supports screen shake."""

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        world_width: float = 3000.0,
        world_height: float = 2000.0,
        smoothness: float = 0.08,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_width = world_width
        self.world_height = world_height
        self.smoothness = smoothness

        # Camera position (top-left coordinates)
        self.x = 0.0
        self.y = 0.0

        # Target position
        self._target_x = 0.0
        self._target_y = 0.0

        # Shake
        self._shake_intensity = 0.0
        self._shake_duration = 0.0
        self._shake_timer = 0.0

        # Parallax background offset
        self._parallax_offsets: list[float] = [0.0, 0.0, 0.0]

    def set_target(self, target_x: float, target_y: float) -> None:
        """Set the target position for the camera to follow (world coordinates)."""
        self._target_x = target_x
        self._target_y = target_y

    def update(self, dt: float) -> None:
        """Update camera position (smooth follow + shake)."""
        # Smooth follow
        desired_x = self._target_x - self.screen_width / 2
        desired_y = self._target_y - self.screen_height / 2

        # Clamp within world bounds
        max_x = max(0, self.world_width - self.screen_width)
        max_y = max(0, self.world_height - self.screen_height)

        desired_x = max(0, min(desired_x, max_x))
        desired_y = max(0, min(desired_y, max_y))

        self.x += (desired_x - self.x) * self.smoothness
        self.y += (desired_y - self.y) * self.smoothness

        # Shake decay
        if self._shake_timer > 0:
            self._shake_timer -= dt
            decay = self._shake_timer / self._shake_duration if self._shake_duration > 0 else 0
            self._shake_intensity *= decay
            if self._shake_timer <= 0:
                self._shake_intensity = 0.0
                self._shake_timer = 0.0

        # Update parallax offsets
        for i in range(len(self._parallax_offsets)):
            factor = 0.1 * (i + 1)
            self._parallax_offsets[i] = self.x * factor

    def shake(self, intensity: float, duration: float) -> None:
        """Trigger screen shake.

        Args:
            intensity: Shake intensity (pixels)
            duration: Duration (seconds)
        """
        self._shake_intensity = intensity
        self._shake_duration = duration
        self._shake_timer = duration

    def get_offset(self) -> tuple[float, float]:
        """Get current camera offset (including shake)."""
        shake_x = 0.0
        shake_y = 0.0
        if self._shake_intensity > 0:
            shake_x = random.uniform(-self._shake_intensity, self._shake_intensity)
            shake_y = random.uniform(-self._shake_intensity, self._shake_intensity)
        return (self.x + shake_x, self.y + shake_y)

    def get_parallax_offset(self, layer: int) -> float:
        """Get offset for the specified parallax layer."""
        if 0 <= layer < len(self._parallax_offsets):
            return self._parallax_offsets[layer]
        return 0.0

    def apply(self, screen: pygame.Surface, surface: pygame.Surface) -> None:
        """Draw the world surface to the screen, applying camera offset."""
        offset_x, offset_y = self.get_offset()
        screen.blit(surface, (-int(offset_x), -int(offset_y)))

    def world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float]:
        """Convert world coordinates to screen coordinates."""
        offset_x, offset_y = self.get_offset()
        return (world_x - offset_x, world_y - offset_y)

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        offset_x, offset_y = self.get_offset()
        return (screen_x + offset_x, screen_y + offset_y)
