from .power_up import PowerUp


class DoubleScorePower(PowerUp):
    """双倍分数道具。"""

    def __init__(self, x, y, config):
        super().__init__(x, y, config.double_score_image, config.double_score_speed)

    def activate(self, player):
        self.collect()
        player.activate_double_score()
