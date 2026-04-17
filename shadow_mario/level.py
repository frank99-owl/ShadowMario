import math
from .io_utils import read_csv
from .entities.player import Player
from .entities.platform import Platform
from .entities.flying_platform import FlyingPlatform
from .entities.enemy import Enemy
from .entities.enemy_boss import EnemyBoss
from .entities.coin import Coin
from .entities.invincible_power import InvinciblePower
from .entities.double_score_power import DoubleScorePower
from .entities.fireball import Fireball
from .entities.end_flag import EndFlag


class Level:
    """管理单个关卡的所有实体和逻辑。"""

    PLATFORM_RIGHT_BOUND = 3000

    def __init__(self, csv_path, config):
        self.config = config
        self.player = None
        self.platforms = []
        self.end_flags = []
        self.enemies = []
        self.coins = []
        self.power_ups = []
        self.fireballs = []
        self.boss = None
        self.current_flying_platform = None

        self.is_win = False
        self.is_loss = False

        data = read_csv(csv_path)
        for row in data:
            entity_type = row[0]
            x = float(row[1])
            y = float(row[2])

            if entity_type == "PLAYER":
                self.player = Player(x, y, config)
            elif entity_type == "PLATFORM":
                self.platforms.append(Platform(x, y, config))
            elif entity_type == "FLYING_PLATFORM":
                self.platforms.append(FlyingPlatform(x, y, config))
            elif entity_type == "END_FLAG":
                self.end_flags.append(EndFlag(x, y, config))
            elif entity_type == "ENEMY":
                self.enemies.append(Enemy(x, y, config))
            elif entity_type == "COIN":
                self.coins.append(Coin(x, y, config))
            elif entity_type == "DOUBLE_SCORE":
                self.power_ups.append(DoubleScorePower(x, y, config))
            elif entity_type == "INVINCIBLE_POWER":
                self.power_ups.append(InvinciblePower(x, y, config))
            elif entity_type == "ENEMY_BOSS":
                self.boss = EnemyBoss(x, y, config)

    @staticmethod
    def check_collision(e1, r1, e2, r2):
        dist = math.sqrt((e1.x - e2.x) ** 2 + (e1.y - e2.y) ** 2)
        return dist <= (r1 + r2)

    def update(self, keys, s_just_pressed, screen):
        self.player.update(keys)

        # 玩家发射火球
        if (self.player.health > 0 and s_just_pressed and self.boss is not None
                and abs(self.player.x - self.boss.x) < self.config.boss_activation_radius):
            direction = 1 if self.boss.x > self.player.x else -1
            self.fireballs.append(Fireball(
                self.player.x, self.player.y, self.config, direction, True
            ))

        # Boss 发射火球
        if (self.boss is not None and self.player.health > 0
                and self.boss.should_shoot(self.player.x, self.config.boss_activation_radius)):
            direction = 1 if self.player.x > self.boss.x else -1
            self.fireballs.append(Fireball(
                self.boss.x, self.boss.y, self.config, direction, False
            ))

        # 玩家站在飞行平台上时同步水平位置
        if self.current_flying_platform is not None and self.player.health > 0:
            self.player.x += self.current_flying_platform.last_random_move

        touching_any_platform = False
        for p in self.platforms:
            p.update(keys)
            p.draw(screen)

            if self.player.health > 0:
                player_rect = self.player.get_bounding_box()
                platform_rect = p.get_bounding_box()

                if isinstance(p, FlyingPlatform):
                    dx = abs(self.player.x - p.x)
                    dy = p.y - self.player.y
                    if (dx < self.config.flying_platform_half_length
                            and dy <= self.config.flying_platform_half_height + 0.01
                            and dy >= (self.config.flying_platform_half_height - 1)
                            and self.player.get_vertical_speed() >= 0):
                        self.player.land_on_platform(p.y - self.config.flying_platform_half_height)
                        touching_any_platform = True
                        self.current_flying_platform = p
                else:
                    horizontal_overlap = (player_rect.left < platform_rect.right
                                          and player_rect.right > platform_rect.left)
                    vertical_overlap = (player_rect.bottom >= platform_rect.top
                                        and player_rect.top < platform_rect.bottom)
                    if horizontal_overlap and vertical_overlap and self.player.get_vertical_speed() >= 0:
                        if self.player.y < p.y:
                            land_y = platform_rect.top - (player_rect.bottom - player_rect.top) / 2.0
                            self.player.land_on_platform(land_y)
                            touching_any_platform = True
                            self.current_flying_platform = None

        if not touching_any_platform and self.player.health > 0:
            self.player.is_jumping = True
            self.current_flying_platform = None

        for e in self.enemies:
            e.update(keys)
            e.draw(screen)
            if (self.player.health > 0
                    and self.check_collision(self.player, self.config.player_radius, e, self.config.enemy_radius)
                    and e.can_inflict_damage()
                    and not self.player.is_invincible()):
                self.player.health -= self.config.enemy_damage
                e.set_has_inflicted_damage(True)

        for c in self.coins:
            c.update(keys)
            c.draw(screen)
            if (self.check_collision(self.player, self.config.player_radius, c, self.config.coin_radius)
                    and not c.is_collected()):
                c.collect()
                self.player.add_score(self.config.coin_value)

        for pu in self.power_ups:
            pu.update(keys)
            pu.draw(screen)
            r = self.config.double_score_radius if isinstance(pu, DoubleScorePower) else self.config.invincible_radius
            if self.check_collision(self.player, self.config.player_radius, pu, r) and not pu.is_collected():
                pu.activate(self.player)

        if self.boss is not None:
            self.boss.update(keys)
            self.boss.draw(screen)

        i = 0
        while i < len(self.fireballs):
            fb = self.fireballs[i]
            fb.update(keys)
            fb.draw(screen)

            if fb.is_shot_by_player():
                if (self.boss is not None
                        and self.check_collision(fb, self.config.fireball_radius, self.boss, self.config.boss_radius)
                        and self.boss.health > 0):
                    self.boss.health -= self.config.fireball_damage
                    fb.active = False
            else:
                if (self.player.health > 0
                        and self.check_collision(fb, self.config.fireball_radius, self.player, self.config.player_radius)
                        and not self.player.is_invincible()):
                    self.player.health -= self.config.fireball_damage
                    fb.active = False

            if not fb.active:
                self.fireballs.pop(i)
            else:
                i += 1

        for f in self.end_flags:
            f.update(keys)
            f.draw(screen)
            if (self.player.health > 0
                    and self.check_collision(self.player, self.config.player_radius, f, self.config.end_flag_radius)):
                if self.boss is None or self.boss.health <= 0:
                    self.is_win = True

        self.player.draw(screen)
        self._draw_status(screen)

        if self.player.y > self.config.window_height:
            self.is_loss = True

    def _draw_status(self, screen):
        font = self.config.status_font
        score_text = f"SCORE {self.player.score}"
        health_text = f"HEALTH {int(round(self.player.health * 100))}"

        score_surf = font.render(score_text, True, (255, 255, 255))
        health_surf = font.render(health_text, True, (255, 255, 255))

        screen.blit(score_surf, (self.config.score_x, self.config.score_y))
        screen.blit(health_surf, (self.config.player_health_x, self.config.player_health_y))

        if self.boss is not None and self.boss.health > 0:
            boss_health_text = f"HEALTH {int(round(self.boss.health * 100))}"
            boss_surf = font.render(boss_health_text, True, (255, 0, 0))
            screen.blit(boss_surf, (self.config.enemy_boss_health_x, self.config.enemy_boss_health_y))
