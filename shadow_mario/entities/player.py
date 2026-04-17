import pygame
from .game_entity import GameEntity


class Player(GameEntity):
    """玩家角色。"""

    def __init__(self, x, y, config):
        super().__init__(x, y, config.player_image_right)
        self.image_left = pygame.image.load(config.player_image_left).convert_alpha()
        self.image_right = pygame.image.load(config.player_image_right).convert_alpha()
        self.facing_right = True
        self.health = config.player_health
        self.score = 0
        self.invincibility_frames = 0
        self.double_score_frames = 0
        self.max_invincibility_frames = config.invincible_max_frames
        self.max_double_score_frames = config.double_score_max_frames
        self.vertical_speed = 0
        self.is_jumping = True
        self._jump_pressed_last_frame = False

    def update(self, keys):
        # 道具计时器
        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1
        if self.double_score_frames > 0:
            self.double_score_frames -= 1

        if self.health <= 0:
            self.y += 2.0
            return

        # 左右朝向（镜像切换）
        if keys[pygame.K_RIGHT]:
            self.facing_right = True
        elif keys[pygame.K_LEFT]:
            self.facing_right = False

        # 跳跃（wasPressed 模拟）
        jump_pressed = keys[pygame.K_UP]
        if jump_pressed and not self._jump_pressed_last_frame and not self.is_jumping:
            self.vertical_speed = -20
            self.is_jumping = True
        self._jump_pressed_last_frame = jump_pressed

        # 垂直移动 + 重力
        if self.is_jumping:
            self.y += self.vertical_speed
            self.vertical_speed += 1.0

    def draw(self, screen):
        current_image = self.image_right if self.facing_right else self.image_left
        rect = current_image.get_rect(center=(self.x, self.y))
        screen.blit(current_image, rect)

    def land_on_platform(self, platform_y):
        self.y = platform_y
        self.vertical_speed = 0
        self.is_jumping = False

    def add_score(self, points):
        self.score += points * 2 if self.double_score_frames > 0 else points

    def activate_invincibility(self):
        self.invincibility_frames = self.max_invincibility_frames

    def activate_double_score(self):
        self.double_score_frames = self.max_double_score_frames

    def is_invincible(self):
        return self.invincibility_frames > 0

    def get_vertical_speed(self):
        return self.vertical_speed

    def get_bounding_box(self):
        current_image = self.image_right if self.facing_right else self.image_left
        return current_image.get_rect(center=(self.x, self.y))
