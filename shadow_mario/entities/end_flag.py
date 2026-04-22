from shadow_mario.config import GameConfig
from .moveable_entity import MoveableEntity


class EndFlag(MoveableEntity):
    """End flag."""

    def __init__(self, x: float, y: float, config: GameConfig) -> None:
        super().__init__(x, y, config.end_flag_image, config.end_flag_speed, hitbox_scale=0.6)
