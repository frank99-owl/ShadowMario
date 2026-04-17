import pygame


class GameEntity:
    """所有游戏实体的抽象基类。"""

    def __init__(self, x, y, image_path):
        self._x = x
        self._y = y
        self.image = pygame.image.load(image_path).convert_alpha()
        self.active = True

    def draw(self, screen):
        if self.active:
            rect = self.image.get_rect(center=(self._x, self._y))
            screen.blit(self.image, rect)

    def update(self, keys):
        raise NotImplementedError

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    def get_bounding_box(self):
        return self.image.get_rect(center=(self._x, self._y))
