from .platform import Platform


class FlyingPlatform(Platform):
    """Flying platform that moves back and forth within a fixed range."""

    def __init__(self, x, y, config, scroll_with_world=True, randomize_direction=True, initial_direction=None):
        super().__init__(x, y, config, config.flying_platform_image, config.flying_platform_speed)
        self.scroll_with_world = scroll_with_world
        self.random_speed = config.flying_platform_random_speed
        self.max_displacement = config.flying_platform_max_displacement
        self.current_displacement = 0
        if initial_direction in (-1, 1):
            self.direction = initial_direction
        elif randomize_direction:
            import random
            self.direction = 1 if random.choice([True, False]) else -1
        else:
            self.direction = 1
        self.last_random_move = 0

    def can_move_right(self):
        return True

    def _advance_motion(self):
        """Move in fixed range with constant speed."""
        move_amount = self.direction * self.random_speed
        self.x += move_amount
        self.current_displacement += move_amount
        self.last_random_move = move_amount

        if abs(self.current_displacement) >= self.max_displacement:
            self.direction *= -1
            if self.current_displacement > self.max_displacement:
                self.current_displacement = self.max_displacement
            elif self.current_displacement < -self.max_displacement:
                self.current_displacement = -self.max_displacement

    def update_flying(self):
        """Horizontal movement only (no background scroll)."""
        self._advance_motion()

    def update(self, keys):
        # Apply world scroll first (optional).
        if self.scroll_with_world:
            super().update(keys)

        # Move at a constant speed in a fixed range.
        self._advance_motion()
