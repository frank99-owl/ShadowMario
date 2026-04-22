"""Focused collaborators used by Level."""

from dataclasses import dataclass
from typing import Callable, Iterable

import pygame

from .entities.coin import Coin
from .entities.double_score_power import DoubleScorePower
from .entities.end_flag import EndFlag
from .entities.enemy import Enemy
from .entities.enemy_boss import EnemyBoss
from .entities.fireball import Fireball
from .entities.flying_platform import FlyingPlatform
from .entities.invincible_power import InvinciblePower
from .entities.platform import Platform
from .entities.player import Player
from .io_utils import read_csv


@dataclass
class LevelEntities:
    """Container for level entity collections."""

    player: Player | None
    player2: Player | None
    platforms: list[Platform]
    end_flags: list[EndFlag]
    enemies: list[Enemy]
    coins: list[Coin]
    power_ups: list[DoubleScorePower | InvinciblePower]
    fireballs: list[Fireball]
    boss: EnemyBoss | None


class LevelEntityLoader:
    """Build entity collections from CSV level data."""

    @staticmethod
    def load(csv_path: str, config, level_number: int) -> LevelEntities:
        data = read_csv(csv_path)
        player_count = 0
        player = None
        player2 = None
        platforms: list[Platform] = []
        end_flags: list[EndFlag] = []
        enemies: list[Enemy] = []
        coins: list[Coin] = []
        power_ups: list[DoubleScorePower | InvinciblePower] = []
        boss: EnemyBoss | None = None

        for row in data:
            entity_type = row[0]
            x = float(row[1])
            y = float(row[2])

            if entity_type == "PLAYER":
                if player_count == 0:
                    player = Player(
                        x,
                        y,
                        config,
                        is_player2=False,
                        swap_controls=(level_number == 4),
                        legacy_movement=(level_number != 4),
                    )
                elif player_count == 1 and level_number == 4:
                    player2 = Player(
                        x,
                        y,
                        config,
                        is_player2=True,
                        swap_controls=(level_number == 4),
                    )
                player_count += 1
            elif entity_type == "PLATFORM":
                platforms.append(Platform(x, y, config))
            elif entity_type == "FLYING_PLATFORM":
                platforms.append(FlyingPlatform(x, y, config))
            elif entity_type == "END_FLAG":
                end_flags.append(EndFlag(x, y, config))
            elif entity_type == "ENEMY":
                enemies.append(Enemy(x, y, config))
            elif entity_type == "COIN":
                coins.append(Coin(x, y, config, allow_respawn=(level_number == 4)))
            elif entity_type == "DOUBLE_SCORE":
                power_ups.append(DoubleScorePower(x, y, config))
            elif entity_type == "INVINCIBLE_POWER":
                power_ups.append(InvinciblePower(x, y, config))
            elif entity_type == "ENEMY_BOSS":
                boss = EnemyBoss(x, y, config)

        return LevelEntities(
            player=player,
            player2=player2,
            platforms=platforms,
            end_flags=end_flags,
            enemies=enemies,
            coins=coins,
            power_ups=power_ups,
            fireballs=[],
            boss=boss,
        )


class PlatformContactResolver:
    """Collision and landing rules for platforms."""

    def __init__(self, config, on_land: Callable[[Player], None]) -> None:
        self.config = config
        self._on_land = on_land

    def try_land(self, player: Player, platform: Platform) -> tuple[bool, FlyingPlatform | None]:
        player_rect = player.get_bounding_box()
        player_half_h = player_rect.height / 2.0
        prev_y = player.y - player.get_vertical_speed()
        prev_bottom = prev_y + player_half_h
        curr_bottom = player.y + player_half_h
        platform_rect = platform.get_bounding_box()
        horizontal_overlap = player_rect.left < platform_rect.right and player_rect.right > platform_rect.left
        crossed_top = prev_bottom <= platform_rect.top + 6 and curr_bottom >= platform_rect.top - 2
        if horizontal_overlap and crossed_top and player.get_vertical_speed() >= 0:
            was_in_air = player.is_jumping
            land_y = platform_rect.top - player_half_h
            player.land_on_platform(land_y)
            if was_in_air:
                self._on_land(player)
            return True, platform if isinstance(platform, FlyingPlatform) else None
        return False, None

    def try_land_legacy_l23(self, player: Player, platform: Platform) -> tuple[bool, FlyingPlatform | None]:
        """Legacy L2/L3 landing behavior from historical implementation."""
        player_rect = player.get_bounding_box()
        platform_rect = platform.get_bounding_box()
        was_in_air = player.is_jumping

        if isinstance(platform, FlyingPlatform):
            dx = abs(player.x - platform.x)
            dy = platform.y - player.y
            if (
                dx < self.config.flying_platform_half_length
                and dy <= self.config.flying_platform_half_height + 0.01
                and dy >= (self.config.flying_platform_half_height - 1)
                and player.get_vertical_speed() >= 0
            ):
                player.land_on_platform(platform.y - self.config.flying_platform_half_height)
                if was_in_air:
                    self._on_land(player)
                return True, platform
            return False, None

        horizontal_overlap = player_rect.left < platform_rect.right and player_rect.right > platform_rect.left
        vertical_overlap = player_rect.bottom >= platform_rect.top and player_rect.top < platform_rect.bottom
        if horizontal_overlap and vertical_overlap and player.get_vertical_speed() >= 0:
            if player.y < platform.y:
                land_y = platform_rect.top - (player_rect.bottom - player_rect.top) / 2.0
                player.land_on_platform(land_y)
                if was_in_air:
                    self._on_land(player)
                return True, None

        return False, None

    def update_platform_contacts(
        self,
        players: Iterable[Player],
        platforms: list[Platform],
        keys,
        scroll_static_platforms: bool,
    ) -> tuple[dict[int, bool], dict[int, FlyingPlatform | None]]:
        """Shared platform update/collision pipeline used by level 4."""
        for platform in platforms:
            if isinstance(platform, FlyingPlatform):
                platform.update_flying()
            elif scroll_static_platforms:
                platform.update(keys)

        touching_any_platform = {id(p): False for p in players}
        flying_plats = {id(p): None for p in players}

        for platform in platforms:
            for player in players:
                if player.health <= 0 or touching_any_platform[id(player)]:
                    continue
                landed, flying_platform = self.try_land(player, platform)
                if landed:
                    touching_any_platform[id(player)] = True
                    flying_plats[id(player)] = flying_platform

        for player in players:
            fp = flying_plats[id(player)]
            if fp is not None and player.health > 0:
                player.x += fp.last_random_move
            if not touching_any_platform[id(player)] and player.health > 0:
                player.is_jumping = True

        return touching_any_platform, flying_plats


class LevelHudRenderer:
    """HUD renderer shared across level modes."""

    def __init__(self, config, health_color: tuple[int, int, int], inv_color: tuple[int, int, int]) -> None:
        self.config = config
        self.health_color = health_color
        self.inv_color = inv_color

    def draw_status(self, screen: pygame.Surface, player: Player, boss: EnemyBoss | None) -> None:
        font = self.config.status_font
        score_text = f"SCORE {player.score}"
        health_text = f"HEALTH {int(round(player.health * 100))}"
        score_surf = font.render(score_text, True, (255, 255, 255))
        health_surf = font.render(health_text, True, (255, 255, 255))

        screen.blit(score_surf, (self.config.score_x, self.config.score_y))
        screen.blit(health_surf, (self.config.player_health_x, self.config.player_health_y))
        self.draw_player_bars(
            screen,
            player=player,
            x=20,
            y=84,
            health_max=max(1.0, self.config.player_health),
        )

        if boss is not None and boss.health > 0:
            boss_health_text = f"HEALTH {int(round(boss.health * 100))}"
            boss_surf = font.render(boss_health_text, True, (255, 0, 0))
            screen.blit(boss_surf, (self.config.enemy_boss_health_x, self.config.enemy_boss_health_y))

    def draw_player_bars(self, screen: pygame.Surface, player: Player, x: int, y: int, health_max: float) -> None:
        bar_w = 200
        bar_h = 10
        gap = 6

        health_ratio = 0.0 if health_max <= 0 else max(0.0, min(1.0, player.health / health_max))
        bg = pygame.Rect(x, y, bar_w, bar_h)
        fg = pygame.Rect(x, y, int(bar_w * health_ratio), bar_h)
        pygame.draw.rect(screen, (25, 25, 30), bg, border_radius=3)
        if fg.width > 0:
            pygame.draw.rect(screen, self.health_color, fg, border_radius=3)
        pygame.draw.rect(screen, (210, 210, 210), bg, 1, border_radius=3)

        inv_ratio = 0.0
        if player.max_invincibility_frames > 0:
            inv_ratio = max(0.0, min(1.0, player.invincibility_frames / player.max_invincibility_frames))
        inv_bg = pygame.Rect(x, y + bar_h + gap, bar_w, bar_h)
        inv_fg = pygame.Rect(x, y + bar_h + gap, int(bar_w * inv_ratio), bar_h)
        pygame.draw.rect(screen, (25, 25, 30), inv_bg, border_radius=3)
        if inv_fg.width > 0:
            pygame.draw.rect(screen, self.inv_color, inv_fg, border_radius=3)
        pygame.draw.rect(screen, (210, 210, 210), inv_bg, 1, border_radius=3)
