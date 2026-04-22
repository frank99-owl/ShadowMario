"""Scene transition effects."""

import pygame


class FadeTransition:
    """Fade in/out transition between scenes.

    Usage:
        transition = FadeTransition()
        # In update:
        transition.update(dt)
        # In draw (after drawing the scene):
        transition.draw(screen)
        # Trigger fade out:
        transition.start_fade_out(duration=0.5)
        # Trigger fade in:
        transition.start_fade_in(duration=0.5)
    """

    def __init__(self, color: tuple = (0, 0, 0)) -> None:
        self.color = color
        self._alpha = 0
        self._target_alpha = 0
        self._speed = 0  # alpha change per second
        self._active = False
        self._callback = None
        self._surface: pygame.Surface | None = None

    def start_fade_out(self, duration: float = 0.5, callback=None) -> None:
        """Start fading to black. Call callback when fully black."""
        self._target_alpha = 255
        self._speed = 255 / duration if duration > 0 else 9999
        self._active = True
        self._callback = callback

    def start_fade_in(self, duration: float = 0.5, callback=None) -> None:
        """Start fading from black to transparent."""
        self._alpha = 255
        self._target_alpha = 0
        self._speed = 255 / duration if duration > 0 else 9999
        self._active = True
        self._callback = callback

    def is_active(self) -> bool:
        return self._active

    def update(self, dt: float) -> None:
        if not self._active:
            return

        if self._alpha < self._target_alpha:
            self._alpha = min(self._target_alpha, self._alpha + self._speed * dt)
        elif self._alpha > self._target_alpha:
            self._alpha = max(self._target_alpha, self._alpha - self._speed * dt)

        if self._alpha == self._target_alpha:
            self._active = False
            if self._callback:
                cb = self._callback
                self._callback = None
                cb()

    def draw(self, screen: pygame.Surface) -> None:
        if self._alpha <= 0:
            return

        if self._surface is None or self._surface.get_size() != screen.get_size():
            self._surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

        self._surface.fill(self.color + (int(self._alpha),))
        screen.blit(self._surface, (0, 0))
