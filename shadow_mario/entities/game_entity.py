"""Game entity base class."""

import pygame



class GameEntity:
    """Abstract base class for all game entities."""

    def __init__(self, x: float, y: float, image_path: str) -> None:
        self._x = x
        self._y = y
        self.image = pygame.image.load(image_path).convert_alpha()
        self.active = True

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
