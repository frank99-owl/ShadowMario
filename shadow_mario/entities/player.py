import pygame

from shadow_mario.config import GameConfig
from .game_entity import GameEntity


class Player(GameEntity):
    """Player character with forgiving jump physics."""

    COYOTE_TIME = 0.12  # Seconds after leaving platform where you can still jump
    JUMP_BUFFER = 0.08  # Seconds before landing where jump input is buffered
    GRAVITY = 0.6
    JUMP_VELOCITY = -16.5
    MAX_FALL_SPEED = 12.0

    MOVE_SPEED = 5.0

    # Levels 1-3 keep the original spec's arc (-20 px/tick, +1 px/tick per tick)
    # and add the forgiveness the spec lacked. Velocities stay integers so
    # positions stay on whole pixels.
    LEGACY_JUMP_VELOCITY = -20.0
    LEGACY_GRAVITY = 1.0
    # Releasing UP while rising faster than this caps the rise: a tap is a hop
    # (about 75 px), a hold is the full 210 px jump.
    LEGACY_JUMP_CUT_VELOCITY = -10.0
    LEGACY_COYOTE_TICKS = 6  # a jump still counts this many ticks after walking off an edge
    LEGACY_BUFFER_TICKS = 6  # a press this many ticks before landing jumps on touchdown

    # Squash and stretch are drawn only; they never change collisions.
    SQUASH_DECAY = 0.72
    JUMP_STRETCH = -0.22
    LAND_SQUASH_PER_SPEED = 0.018
    LAND_SQUASH_MAX = 0.32
    HURT_FLASH_TICKS = 14

    def __init__(self, x: float, y: float, config: GameConfig, is_player2: bool = False,
                 swap_controls: bool = False, legacy_movement: bool = False) -> None:
        super().__init__(x, y, config.player_image_right)
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
        self.score = 0
        self.invincibility_frames = 0
        self.double_score_frames = 0
        self.max_invincibility_frames = config.invincible_max_frames
        self.max_double_score_frames = config.double_score_max_frames
        self.vertical_speed = 0.0
        self.is_jumping = True
        self._jump_pressed_last_frame = False

        # Spawn position (level 1 hints measure travel from it)
        self.spawn_x = x
        self.spawn_y = y

        # Coyote time: time since left platform
        self._coyote_timer = 0.0
        self._was_grounded = False

        # Jump buffer: time since jump was pressed while in air
        self._jump_buffer_timer = 0.0

        # Legacy (levels 1-3) forgiveness counters, in ticks
        self._buffer_ticks = 0
        self._air_ticks = 0
        self._jumped_since_ground = False

        # Read by Level after update(): a jump started this tick
        self.jumped_this_tick = False
        self.prev_y = y
        self.last_impact_speed = 0.0

        # Draw-only feedback state
        self._squash = 0.0
        self._hurt_flash_ticks = 0

    def update(self, keys) -> None:
        self.prev_y = self.y
        self.jumped_this_tick = False
        self._squash *= self.SQUASH_DECAY
        if abs(self._squash) < 0.01:
            self._squash = 0.0
        if self._hurt_flash_ticks > 0:
            self._hurt_flash_ticks -= 1

        # Power-up timers
        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1
        if self.double_score_frames > 0:
            self.double_score_frames -= 1

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
        """Original-spec jump arc plus buffer, coyote time and a variable height."""
        if jump_pressed and not self._jump_pressed_last_frame:
            self._buffer_ticks = self.LEGACY_BUFFER_TICKS
        elif self._buffer_ticks > 0:
            self._buffer_ticks -= 1
        self._jump_pressed_last_frame = jump_pressed

        # is_jumping still holds last tick's platform contact result here.
        if self.is_jumping:
            self._air_ticks += 1
        else:
            self._air_ticks = 0
            self._jumped_since_ground = False

        can_jump = not self.is_jumping or (
            not self._jumped_since_ground and self._air_ticks <= self.LEGACY_COYOTE_TICKS
        )
        if self._buffer_ticks > 0 and can_jump:
            self._buffer_ticks = 0
            self._jumped_since_ground = True
            self.vertical_speed = self.LEGACY_JUMP_VELOCITY
            self.is_jumping = True
            self._start_jump_feedback()

        if (self._jumped_since_ground and not jump_pressed
                and self.vertical_speed < self.LEGACY_JUMP_CUT_VELOCITY):
            self.vertical_speed = self.LEGACY_JUMP_CUT_VELOCITY

        if self.is_jumping:
            self.y += self.vertical_speed
            self.vertical_speed += self.LEGACY_GRAVITY

    def _do_jump(self) -> None:
        """Execute jump."""
        self.vertical_speed = self.JUMP_VELOCITY
        self.is_jumping = True
        self._start_jump_feedback()

    def _start_jump_feedback(self) -> None:
        self.jumped_this_tick = True
        self._squash = self.JUMP_STRETCH

    def on_land(self) -> None:
        """Squash on touchdown, harder for faster falls."""
        self._squash = min(self.LAND_SQUASH_MAX, self.last_impact_speed * self.LAND_SQUASH_PER_SPEED)

    def on_hurt(self) -> None:
        self._hurt_flash_ticks = self.HURT_FLASH_TICKS
        self._squash = 0.18

    def land_on_platform(self, platform_y: float) -> None:
        """Called when player lands on a platform."""
        self.last_impact_speed = self.vertical_speed
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

    def draw(self, screen: pygame.Surface, offset: tuple[float, float] = (0, 0)) -> None:
        current_image = self.image_right if self.facing_right else self.image_left
        draw_x = int(self.x + offset[0])
        draw_y = int(self.y + offset[1])

        # Keep dead players visible while falling so knockout feedback is readable.
        if self.health <= 0:
            fall_ratio = max(0.0, min(1.0, (self.y - self.spawn_y) / 180.0))
            rotate_dir = -1 if self.facing_right else 1
            angle = 110.0 * fall_ratio * rotate_dir
            dead_img = pygame.transform.rotozoom(current_image, angle, 1.0)
            dead_img.set_alpha(int(230 - 140 * fall_ratio))
            dead_rect = dead_img.get_rect(center=(draw_x, draw_y))
            screen.blit(dead_img, dead_rect)
            return

        if self._squash:
            # Scale around the feet so a squash reads as weight, not as sinking.
            w = max(1, round(current_image.get_width() * (1 + self._squash)))
            h = max(1, round(current_image.get_height() * (1 - self._squash)))
            current_image = pygame.transform.scale(current_image, (w, h))
            rect = current_image.get_rect(midbottom=(draw_x, draw_y + self.image_right.get_height() // 2))
        else:
            rect = current_image.get_rect(center=(draw_x, draw_y))

        if self._hurt_flash_ticks > 0 and self._hurt_flash_ticks % 4 < 2:
            hurt_img = current_image.copy()
            hurt_img.fill((255, 90, 90, 255), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(hurt_img, rect)
            return

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
