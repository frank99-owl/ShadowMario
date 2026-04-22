from shadow_mario.config import GameConfig
from .moveable_entity import MoveableEntity


class Fireball(MoveableEntity):
    """Fireball entity."""

    def __init__(self, x: float, y: float, config: GameConfig,
                 direction: int, shot_by_player: bool) -> None:
        super().__init__(x, y, config.fireball_image, config.platform_speed, hitbox_scale=0.6)
        self.fly_speed = config.fireball_speed
        self.direction = direction  # 1 for right, -1 for left
        self.shot_by_player = shot_by_player
        self.screen_width = config.window_width

    def update(self, keys) -> None:
        super().update(keys)
        self.x += self.direction * self.fly_speed
        if self.x < 0 or self.x > self.screen_width:
            self.active = False

    def is_shot_by_player(self) -> bool:
        return self.shot_by_player
