import random


from shadow_mario.config import GameConfig
from .moveable_entity import MoveableEntity


class EnemyBoss(MoveableEntity):
    """Boss enemy, has health and shoots fireballs."""

    def __init__(self, x: float, y: float, config: GameConfig) -> None:
        super().__init__(x, y, config.boss_image, config.boss_speed, hitbox_scale=0.85)
        self.health = config.boss_health
        self.frame_counter = 0
        self._rand = random.Random()
        self.screen_height = config.window_height

    def update(self, keys) -> None:
        if self.health > 0:
            super().update(keys)
            self.frame_counter += 1
        else:
            self.y += 2.0
            if self.y > self.screen_height:
                self.active = False

    def should_shoot(self, player_x: float, activation_radius: float) -> bool:
        if self.health > 0 and abs(self.x - player_x) >= activation_radius:
            if self.frame_counter % 100 == 0:
                return random.choice([True, False])
        return False
