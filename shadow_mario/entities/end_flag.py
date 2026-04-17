from .moveable_entity import MoveableEntity


class EndFlag(MoveableEntity):
    """终点旗帜。"""

    def __init__(self, x, y, config):
        super().__init__(x, y, config.end_flag_image, config.end_flag_speed)
