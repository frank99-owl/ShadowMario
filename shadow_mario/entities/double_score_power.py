from shadow_mario.config import GameConfig
from .power_up import PowerUp


class DoubleScorePower(PowerUp):
    """Double score power-up, doubles coin rewards."""

    def __init__(self, x: float, y: float, config: GameConfig) -> None:
        super().__init__(x, y, config.double_score_image, config.double_score_speed)

    def activate(self, player) -> None:
        self.collect()
        player.activate_double_score()
