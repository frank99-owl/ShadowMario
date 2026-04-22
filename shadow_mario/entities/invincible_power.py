from shadow_mario.config import GameConfig
from .power_up import PowerUp


class InvinciblePower(PowerUp):
    """Invincible power-up, immune to damage."""

    def __init__(self, x: float, y: float, config: GameConfig) -> None:
        super().__init__(x, y, config.invincible_image, config.invincible_speed)

    def activate(self, player) -> None:
        self.collect()
        player.activate_invincibility()
