from .moveable_entity import MoveableEntity


class PowerUp(MoveableEntity):
    """Abstract base class for power-ups."""

    FLY_SPEED = -10.0

    def __init__(self, x: float, y: float, image_path: str,
                 scroll_speed: float, hitbox_scale: float = 0.7) -> None:
        super().__init__(x, y, image_path, scroll_speed, hitbox_scale)
        self._is_collected = False
        self.vertical_speed = 0.0

    def update(self, keys) -> None:
        if not self._is_collected:
            super().update(keys)
        else:
            self.y += self.vertical_speed
            if self.y < 0:
                self.active = False

    def collect(self) -> None:
        if not self._is_collected:
            self._is_collected = True
            self.vertical_speed = self.FLY_SPEED

    def is_collected(self) -> bool:
        return self._is_collected

    def activate(self, player) -> None:
        raise NotImplementedError
