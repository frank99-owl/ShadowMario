import pygame

from shadow_mario.config import GameConfig
from .game_entity import GameEntity


class Player(GameEntity):
    """Player character with lives system and improved jump physics."""

    MAX_LIVES = 3
    COYOTE_TIME = 0.12  # Seconds after leaving platform where you can still jump
    JUMP_BUFFER = 0.08  # Seconds before landing where jump input is buffered
    GRAVITY = 0.6
    JUMP_VELOCITY = -16.5
    MAX_FALL_SPEED = 12.0

    MOVE_SPEED = 5.0

    def __init__(self, x: float, y: float, config: GameConfig, is_player2: bool = False,
                 swap_controls: bool = False, legacy_movement: bool = False) -> None:
        super().__init__(x, y, config.player_image_right, hitbox_scale=0.75)
        self.is_player2 = is_player2
        self.swap_controls = swap_controls
        self.legacy_movement = legacy_movement
        self.enable_horizontal_move = False
        
        # Color tint for player 2
        img_left = pygame.image.load(config.player_image_left).convert_alpha()
        img_right = pygame.image.load(config.player_image_right).convert_alpha()
        
        if is_player2:
            # Tint player 2 red
            img_left.fill((255, 100, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
            img_right.fill((255, 100, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
            
        self.image_left = img_left
        self.image_right = img_right
        
        self.facing_right = True
        self.health = config.player_health
        self.lives = self.MAX_LIVES
        self.score = 0
        self.invincibility_frames = 0
        self.double_score_frames = 0
        self.max_invincibility_frames = config.invincible_max_frames
        self.max_double_score_frames = config.double_score_max_frames
        self.vertical_speed = 0.0
        self.is_jumping = True
        self._jump_pressed_last_frame = False

        # Spawn position for respawn
        self.spawn_x = x
        self.spawn_y = y

        # Checkpoint position (updated when reaching checkpoints)
        self.checkpoint_x = x
        self.checkpoint_y = y

        # Respawn effect timer (for visual effect)
        self.respawn_effect_timer = 0.0

        # Coyote time: time since left platform
        self._coyote_timer = 0.0
        self._was_grounded = False

        # Jump buffer: time since jump was pressed while in air
        self._jump_buffer_timer = 0.0

    def update(self, keys) -> None:
        # Power-up timers
        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1
        if self.double_score_frames > 0:
            self.double_score_frames -= 1
        if self.respawn_effect_timer > 0:
            self.respawn_effect_timer -= 1 / 60

        if self.health <= 0:
            self.y += 2.0
            return

        # Control scheme: swap_controls swaps P1/P2 key mapping
        # swap_controls=False (default): P1=arrows, P2=WASD
        # swap_controls=True (level 4): P1=WASD, P2=arrows
        use_wasd = (self.swap_controls and not self.is_player2) or \
                   (not self.swap_controls and self.is_player2)

        if use_wasd:
            left_pressed = keys[pygame.K_a]
            right_pressed = keys[pygame.K_d]
            jump_pressed = keys[pygame.K_w]
        else:
            left_pressed = keys[pygame.K_LEFT]
            right_pressed = keys[pygame.K_RIGHT]
            jump_pressed = keys[pygame.K_UP]

        if right_pressed:
            self.facing_right = True
        elif left_pressed:
            self.facing_right = False

        # Horizontal movement (only in camera mode / level 4)
        if self.enable_horizontal_move:
            if right_pressed:
                self.x += self.MOVE_SPEED
            if left_pressed:
                self.x -= self.MOVE_SPEED

        if self.legacy_movement:
            self._update_legacy_jump(jump_pressed)
            return

        # Jump with coyote time and jump buffer

        # Update coyote timer
        if not self.is_jumping:
            self._was_grounded = True
            self._coyote_timer = self.COYOTE_TIME
        else:
            if self._was_grounded:
                self._coyote_timer -= 1 / 60
                if self._coyote_timer <= 0:
                    self._was_grounded = False

        # Jump buffer: if jump pressed while in air, remember it briefly
        if jump_pressed and not self._jump_pressed_last_frame:
            if self.is_jumping:
                self._jump_buffer_timer = self.JUMP_BUFFER
            else:
                # On ground, jump immediately
                self._do_jump()

        # If jump was buffered and we just landed, jump
        if self._jump_buffer_timer > 0:
            self._jump_buffer_timer -= 1 / 60
            if not self.is_jumping:
                self._do_jump()
                self._jump_buffer_timer = 0

        # Normal jump (coyote time allows jumping briefly after leaving platform)
        if jump_pressed and not self._jump_pressed_last_frame:
            if self._coyote_timer > 0 and self.is_jumping:
                self._do_jump()
                self._coyote_timer = 0

        self._jump_pressed_last_frame = jump_pressed

        # Variable jump height: release jump key early for shorter jump
        if not jump_pressed and self.vertical_speed < -4.0:
            self.vertical_speed *= 0.7

        # Vertical movement + gravity with terminal velocity
        self.y += self.vertical_speed
        self.vertical_speed += self.GRAVITY
        if self.vertical_speed > self.MAX_FALL_SPEED:
            self.vertical_speed = self.MAX_FALL_SPEED

        self.is_jumping = True  # Assume in air until platform collision says otherwise

    def _update_legacy_jump(self, jump_pressed: bool) -> None:
        """Legacy jump physics from the original GitHub version."""
        if jump_pressed and not self._jump_pressed_last_frame and not self.is_jumping:
            self.vertical_speed = -20.0
            self.is_jumping = True
        self._jump_pressed_last_frame = jump_pressed

        if self.is_jumping:
            self.y += self.vertical_speed
            self.vertical_speed += 1.0

    def _do_jump(self) -> None:
        """Execute jump."""
        self.vertical_speed = self.JUMP_VELOCITY
        self.is_jumping = True

    def land_on_platform(self, platform_y: float) -> None:
        """Called when player lands on a platform."""
        self.y = platform_y
        self.vertical_speed = 0.0
        self.is_jumping = False
        self._coyote_timer = self.COYOTE_TIME
        self._was_grounded = True

    def take_damage(self, amount: float) -> bool:
        """Take damage. Returns True if player died (health <= 0)."""
        if self.is_invincible():
            return False
        self.health -= amount
        if self.health <= 0:
            return True
        return False

    def respawn(self) -> bool:
        """Respawn player at spawn point. Returns True if lives remain, False if game over."""
        self.lives -= 1
        if self.lives <= 0:
            return False
        # Reset position and health (use checkpoint if available)
        self.x = self.checkpoint_x
        self.y = self.checkpoint_y
        self.health = 1.0
        self.vertical_speed = 0.0
        self.is_jumping = True
        self.invincibility_frames = 120  # 2 seconds of invincibility after respawn
        self.respawn_effect_timer = 1.0  # 1 second respawn visual effect
        return True

    def draw(self, screen: pygame.Surface, offset: tuple[float, float] = (0, 0)) -> None:
        current_image = self.image_right if self.facing_right else self.image_left
        draw_x = int(self.x + offset[0])
        draw_y = int(self.y + offset[1])

        # Keep dead players visible while falling so knockout feedback is readable.
        if self.health <= 0:
            fall_ratio = max(0.0, min(1.0, (self.y - self.checkpoint_y) / 180.0))
            rotate_dir = -1 if self.facing_right else 1
            angle = 110.0 * fall_ratio * rotate_dir
            dead_img = pygame.transform.rotozoom(current_image, angle, 1.0)
            dead_img.set_alpha(int(230 - 140 * fall_ratio))
            dead_rect = dead_img.get_rect(center=(draw_x, draw_y))
            screen.blit(dead_img, dead_rect)
            return

        rect = current_image.get_rect(center=(draw_x, draw_y))

        # Invincibility flashing effect
        if self.invincibility_frames > 0 and self.invincibility_frames % 6 < 3:
            alpha_img = current_image.copy()
            alpha_img.set_alpha(100)
            screen.blit(alpha_img, rect)
        else:
            screen.blit(current_image, rect)

    def add_score(self, points: int) -> None:
        self.score += points * 2 if self.double_score_frames > 0 else points

    def activate_invincibility(self) -> None:
        self.invincibility_frames = self.max_invincibility_frames

    def activate_double_score(self) -> None:
        self.double_score_frames = self.max_double_score_frames

    def is_invincible(self) -> bool:
        return self.invincibility_frames > 0

    def get_vertical_speed(self) -> float:
        return self.vertical_speed

    def get_bounding_box(self) -> pygame.Rect:
        current_image = self.image_right if self.facing_right else self.image_left
        return current_image.get_rect(center=(self.x, self.y))
