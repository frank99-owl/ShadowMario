from .power_up import PowerUp


class InvinciblePower(PowerUp):
    """无敌道具。"""

    def __init__(self, x, y, config):
        super().__init__(x, y, config.invincible_image, config.invincible_speed)

    def activate(self, player):
        self.collect()
        player.activate_invincibility()
