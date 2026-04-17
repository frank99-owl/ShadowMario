from .moveable_entity import MoveableEntity


class PowerUp(MoveableEntity):
    """道具抽象基类。"""

    FLY_SPEED = -10.0

    def __init__(self, x, y, image_path, scroll_speed):
        super().__init__(x, y, image_path, scroll_speed)
        self._is_collected = False
        self.vertical_speed = 0

    def update(self, keys):
        if not self._is_collected:
            super().update(keys)
        else:
            self.y += self.vertical_speed
            if self.y < 0:
                self.active = False

    def collect(self):
        if not self._is_collected:
            self._is_collected = True
            self.vertical_speed = self.FLY_SPEED

    def is_collected(self):
        return self._is_collected

    def activate(self, player):
        raise NotImplementedError
