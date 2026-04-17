from .moveable_entity import MoveableEntity


class Fireball(MoveableEntity):
    """火球实体。"""

    def __init__(self, x, y, config, direction, shot_by_player):
        super().__init__(x, y, config.fireball_image, config.platform_speed)
        self.fly_speed = config.fireball_speed
        self.direction = direction  # 1 for right, -1 for left
        self.shot_by_player = shot_by_player
        self.screen_width = config.window_width

    def update(self, keys):
        super().update(keys)
        self.x += self.direction * self.fly_speed
        if self.x < 0 or self.x > self.screen_width:
            self.active = False

    def is_shot_by_player(self):
        return self.shot_by_player
