import math
from dataclasses import dataclass

import pygame

from .audio import get_audio_manager
from .entities.double_score_power import DoubleScorePower
from .entities.fireball import Fireball
from .level_components import LevelEntityLoader, LevelHudRenderer, PlatformContactResolver
from .particles import ParticleSystem


class _NoKeys:
    """Key-like object that always returns False."""

    def __getitem__(self, _):
        return False


@dataclass(frozen=True)
class LevelSnapshot:
    """Read-only frame snapshot for scene-side consumers."""

    level_number: int
    camera_mode: bool
    is_win: bool
    is_loss: bool
    race_winner: int | None
    score: int
    health: float
    p1_score: int
    p2_score: int
    elapsed_time: float
    total_coins: int
    collected_coins: int
    shake_intensity: float
    combo_count: int
    checkpoint_count: int
    current_checkpoint_idx: int
    has_player2: bool


@dataclass(frozen=True)
class LevelResult:
    """Immutable level result payload model."""

    level: int
    score: int
    health: float
    elapsed_time: float
    total_coins: int
    collected_coins: int
    p1_score: int
    p2_score: int
    race_winner: int | None


class Level:
    """Manage entities and gameplay rules for one level."""

    PLATFORM_RIGHT_BOUND = 3000
    UNIFIED_HEALTH_BAR_COLOR = (100, 240, 120)
    UNIFIED_INV_BAR_COLOR = (90, 180, 255)
    PLAYER_FIRE_COOLDOWN_FRAMES = 8

    def __init__(self, csv_path, config, level_number=1, audio_manager=None):
        self.config = config
        self.level_number = level_number
        self.camera_mode = (level_number == 4)
        self.particles = ParticleSystem()
        self._audio = audio_manager or get_audio_manager()
        self._no_keys = _NoKeys()
        self.player = None
        self.player2 = None
        self.platforms = []
        self.end_flags = []
        self.enemies = []
        self.coins = []
        self.power_ups = []
        self.fireballs = []
        self.boss = None
        self.current_flying_platform = None
        self._contacts = PlatformContactResolver(config, self._on_player_land)
        self._hud_renderer = LevelHudRenderer(
            config,
            health_color=self.UNIFIED_HEALTH_BAR_COLOR,
            inv_color=self.UNIFIED_INV_BAR_COLOR,
        )

        self.is_win = False
        self.is_loss = False
        self.race_winner = None

        # Runtime status read by scenes/HUD.
        self.elapsed_time = 0.0
        self.total_coins = 0
        self.collected_coins_count = 0
        self.shake_intensity = 0.0
        self.combo_count = 0
        self._combo_timer = 0.0
        self._player_fire_cooldown = 0
        self.checkpoints = []
        self.current_checkpoint_idx = -1
        self.best_time = None
        self._boss_death_fx_done = False

        entities = LevelEntityLoader.load(csv_path, config, level_number)
        self.player = entities.player
        self.player2 = entities.player2
        self.platforms = entities.platforms
        self.end_flags = entities.end_flags
        self.enemies = entities.enemies
        self.coins = entities.coins
        self.power_ups = entities.power_ups
        self.fireballs = entities.fireballs
        self.boss = entities.boss

        self._trim_entities_right_of_end_flag()
        self._init_level_specific_state()
        self.total_coins = len(self.coins)

    @staticmethod
    def check_collision(e1, r1, e2, r2):
        dist = math.sqrt((e1.x - e2.x) ** 2 + (e1.y - e2.y) ** 2)
        return dist <= (r1 + r2)

    def _trim_entities_right_of_end_flag(self):
        if not self.end_flags:
            return
        right_limit = min(flag.x for flag in self.end_flags)
        self.platforms = [p for p in self.platforms if p.x <= right_limit]
        self.coins = [c for c in self.coins if c.x <= right_limit]
        self.enemies = [e for e in self.enemies if e.x <= right_limit]
        self.power_ups = [pu for pu in self.power_ups if pu.x <= right_limit]
        if self.boss is not None and self.boss.x > right_limit:
            self.boss = None

    def _init_level_specific_state(self):
        if not self.camera_mode:
            return
        for p in (self.player, self.player2):
            if p is not None:
                p.health = 100.0

    def update(self, keys, s_just_pressed, screen=None):
        frame_dt = 1.0 / 60.0
        if not self.is_win and not self.is_loss:
            self.elapsed_time += frame_dt

        if self.combo_count > 0:
            self._combo_timer -= frame_dt
            if self._combo_timer <= 0:
                self.combo_count = 0
                self._combo_timer = 0.0

        if self._player_fire_cooldown > 0:
            self._player_fire_cooldown -= 1

        if self.shake_intensity > 0:
            self.shake_intensity *= 0.9
            if self.shake_intensity < 0.05:
                self.shake_intensity = 0.0

        if self.camera_mode:
            self._update_race(keys, s_just_pressed)
        else:
            self._update_original(keys, s_just_pressed)

        self.particles.update(frame_dt)
        # Compatibility: old main.py passes screen and expects update+draw together
        if screen is not None:
            self.draw(screen)

    def draw(self, screen, offset=(0, 0)):
        if self.camera_mode:
            self._draw_race(screen, offset)
        else:
            self._draw_original(screen)

    def draw_hud(self, screen):
        if self.camera_mode:
            self._draw_race_hud(screen)
        # Levels 1-3 HUD is already rendered in _draw_original.

    def snapshot(self) -> LevelSnapshot:
        """Return a stable read-only snapshot for scene logic."""
        p1_score = self.player.score if self.player is not None else 0
        p2_score = self.player2.score if self.player2 is not None else 0
        return LevelSnapshot(
            level_number=self.level_number,
            camera_mode=self.camera_mode,
            is_win=self.is_win,
            is_loss=self.is_loss,
            race_winner=self.race_winner,
            score=p1_score,
            health=self.player.health if self.player is not None else 0.0,
            p1_score=p1_score,
            p2_score=p2_score,
            elapsed_time=self.elapsed_time,
            total_coins=self.total_coins,
            collected_coins=self.collected_coins_count,
            shake_intensity=self.shake_intensity,
            combo_count=self.combo_count,
            checkpoint_count=len(self.checkpoints),
            current_checkpoint_idx=self.current_checkpoint_idx,
            has_player2=self.player2 is not None,
        )

    def build_result(self) -> LevelResult:
        """Build typed result data for scene transitions."""
        snapshot = self.snapshot()
        return LevelResult(
            level=snapshot.level_number,
            score=snapshot.score,
            health=snapshot.health,
            elapsed_time=snapshot.elapsed_time,
            total_coins=snapshot.total_coins,
            collected_coins=snapshot.collected_coins,
            p1_score=snapshot.p1_score,
            p2_score=snapshot.p2_score,
            race_winner=snapshot.race_winner,
        )

    def force_race_winner(self, winner: int) -> None:
        """Force race winner and close the level as win."""
        if winner not in (0, 1, 2):
            return
        self.race_winner = winner
        self.is_win = True

    def finalize_race_by_score(self) -> None:
        """Finalize race winner based on score and mark win."""
        self._set_race_winner_by_score()
        self.is_win = True

    # ========== Original levels 1-3 logic ==========

    def _update_original(self, keys, s_just_pressed):
        was_player_jumping = self.player.is_jumping
        self.player.update(keys)
        if (self.player.health > 0 and not was_player_jumping and self.player.is_jumping
                and self.player.get_vertical_speed() < 0):
            self._on_player_jump(self.player)

        # Player shoots fireball.
        shoot_pressed = bool(s_just_pressed or keys[pygame.K_s])
        if (self.player.health > 0 and shoot_pressed and self.boss is not None
                and self._player_fire_cooldown == 0
                and abs(self.player.x - self.boss.x) < self.config.boss_activation_radius):
            direction = 1 if self.player.facing_right else -1
            spawn_offset = 24 if direction > 0 else -24
            self.fireballs.append(Fireball(
                self.player.x + spawn_offset, self.player.y, self.config, direction, True
            ))
            self._audio.play_sfx("shoot")
            self._player_fire_cooldown = self.PLAYER_FIRE_COOLDOWN_FRAMES

        # Boss shoots fireball.
        if (self.boss is not None and self.player.health > 0
                and self.boss.should_shoot(self.player.x, self.config.boss_activation_radius)):
            direction = 1 if self.player.x > self.boss.x else -1
            self.fireballs.append(Fireball(
                self.boss.x, self.boss.y, self.config, direction, False
            ))
            self._audio.play_sfx("shoot")

        # Keep player in sync with moving platform velocity.
        if self.current_flying_platform is not None and self.player.health > 0:
            self.player.x += self.current_flying_platform.last_random_move

        touching_any_platform = False
        for p in self.platforms:
            p.update(keys)

            if self.player.health > 0:
                landed, flying_platform = self._try_land_on_platform_legacy_l23(self.player, p)
                if landed:
                    touching_any_platform = True
                    self.current_flying_platform = flying_platform

        if not touching_any_platform and self.player.health > 0:
            self.player.is_jumping = True
            self.current_flying_platform = None

        for e in self.enemies:
            e.update(keys)
            if (self.player.health > 0
                    and self.check_collision(self.player, self.config.player_radius, e, self.config.enemy_radius)
                    and e.can_inflict_damage()
                    and not self.player.is_invincible()):
                self.player.health -= self.config.enemy_damage
                e.set_has_inflicted_damage(True)
                self._on_damage(self.player.x, self.player.y)

        for c in self.coins:
            c.update(keys)
            if (self.check_collision(self.player, self.config.player_radius, c, self.config.coin_radius)
                    and not c.is_collected()):
                self._collect_coin(self.player, c)

        for pu in self.power_ups:
            pu.update(keys)
            r = self.config.double_score_radius if isinstance(pu, DoubleScorePower) else self.config.invincible_radius
            if self.check_collision(self.player, self.config.player_radius, pu, r) and not pu.is_collected():
                pu.activate(self.player)
                self._audio.play_sfx("powerup")

        if self.boss is not None:
            self.boss.update(keys)
            if self.boss.health <= 0:
                self._trigger_boss_death_fx()

        i = 0
        while i < len(self.fireballs):
            fb = self.fireballs[i]
            fb.update(keys)
            if fb.active:
                self.particles.emit("fireball_trail", fb.x, fb.y, direction=fb.direction)

            if fb.is_shot_by_player():
                if (self.boss is not None
                        and self.check_collision(fb, self.config.fireball_radius, self.boss, self.config.boss_radius)
                        and self.boss.health > 0):
                    self.boss.health -= self.config.fireball_damage
                    self.particles.emit("damage_hit", self.boss.x, self.boss.y)
                    self.shake_intensity = max(self.shake_intensity, 7.0)
                    self._audio.play_sfx("boss_hit")
                    if self.boss.health <= 0:
                        self._trigger_boss_death_fx()
                    fb.active = False
            else:
                if (self.player.health > 0
                        and self.check_collision(fb, self.config.fireball_radius, self.player, self.config.player_radius)
                        and not self.player.is_invincible()):
                    self.player.health -= self.config.fireball_damage
                    self._on_damage(self.player.x, self.player.y)
                    fb.active = False

            if not fb.active:
                self.fireballs.pop(i)
            else:
                i += 1

        for f in self.end_flags:
            f.update(keys)
            if (self.player.health > 0
                    and self.check_collision(self.player, self.config.player_radius, f, self.config.end_flag_radius)):
                if self.boss is None or self.boss.health <= 0:
                    self.is_win = True

        if self.player.y > self.config.window_height:
            self.is_loss = True

    def _draw_original(self, screen):
        for p in self.platforms:
            p.draw(screen)
        for e in self.enemies:
            e.draw(screen)
        for c in self.coins:
            c.draw(screen)
        for pu in self.power_ups:
            pu.draw(screen)
        if self.boss is not None:
            self.boss.draw(screen)
        for fb in self.fireballs:
            fb.draw(screen)
        for f in self.end_flags:
            f.draw(screen)
        self.player.draw(screen)
        self.particles.draw(screen)
        self._draw_status(screen)

    def _draw_status(self, screen):
        if self.player is None:
            return
        self._hud_renderer.draw_status(screen, self.player, self.boss)

    def _on_player_jump(self, player):
        direction = 1 if player.facing_right else -1
        self.particles.emit("jump_dust", player.x, player.y + 28, direction=direction)
        self._audio.play_sfx("jump")

    def _on_player_land(self, player):
        self.particles.emit("land_dust", player.x, player.y + 30)
        self.shake_intensity = max(self.shake_intensity, 1.8)
        self._audio.play_sfx("land")

    def _on_damage(self, x, y):
        self.particles.emit("damage_hit", x, y)
        self.shake_intensity = max(self.shake_intensity, 5.0)
        self._audio.play_sfx("hurt")

    def _on_player_knockout(self, player):
        self.particles.emit("damage_hit", player.x, player.y)
        self.particles.emit("combo_burst", player.x, player.y)
        self.particles.emit("land_dust", player.x, player.y + 24)
        self.shake_intensity = max(self.shake_intensity, 10.0)
        self._audio.play_sfx("hurt")

    def _collect_coin(self, collector, coin):
        coin.collect()
        collector.add_score(self.config.coin_value)
        self.collected_coins_count += 1
        self.combo_count += 1
        self._combo_timer = 1.2
        self.particles.emit("coin_sparkle", coin.x, coin.y)
        if self.combo_count > 0 and self.combo_count % 5 == 0:
            self.particles.emit("combo_burst", collector.x, collector.y - 18)
            self.shake_intensity = max(self.shake_intensity, 2.8)
        self._audio.play_sfx("coin")

    def _trigger_boss_death_fx(self):
        if self.boss is None or self._boss_death_fx_done:
            return
        self._boss_death_fx_done = True
        self.particles.emit("boss_death", self.boss.x, self.boss.y)
        self.shake_intensity = max(self.shake_intensity, 12.0)

    def _set_race_winner(self, winner_player):
        if winner_player is self.player:
            self.race_winner = 1
        elif winner_player is self.player2:
            self.race_winner = 2

    def _set_race_winner_by_score(self):
        if self.player is None or self.player2 is None:
            return
        if self.player.score > self.player2.score:
            self.race_winner = 1
        elif self.player2.score > self.player.score:
            self.race_winner = 2
        else:
            self.race_winner = 0

    def _try_land_on_platform(self, player, platform):
        return self._contacts.try_land(player, platform)

    def _try_land_on_platform_legacy_l23(self, player, platform):
        return self._contacts.try_land_legacy_l23(player, platform)

    def _update_platform_contacts(self, players, keys, scroll_static_platforms):
        return self._contacts.update_platform_contacts(players, self.platforms, keys, scroll_static_platforms)

    # ========== Level 4 race mode logic ==========

    def _update_race(self, keys, s_just_pressed):
        players = [p for p in [self.player, self.player2] if p is not None]
        was_jumping = {id(p): p.is_jumping for p in players}

        # Enable horizontal movement
        for p in players:
            p.enable_horizontal_move = True
            p.update(keys)
            if (p.health > 0 and not was_jumping[id(p)] and p.is_jumping
                    and p.get_vertical_speed() < 0):
                self._on_player_jump(p)

        self._update_platform_contacts(players, keys, scroll_static_platforms=False)

        # Enemy collision (-25 health per hit in race mode)
        for e in self.enemies:
            e.update(self._no_keys)
            for p in players:
                if (p.health > 0
                        and self.check_collision(p, self.config.player_radius, e, self.config.enemy_radius)
                        and e.can_inflict_damage()
                        and not p.is_invincible()):
                    was_alive = p.health > 0
                    p.health -= 25.0
                    if p.health < 0:
                        p.health = 0.0
                    e.set_has_inflicted_damage(True)
                    self._on_damage(p.x, p.y)
                    if was_alive and p.health <= 0:
                        self._on_player_knockout(p)

        # Coin collection (race mode: first to touch gets it)
        for c in self.coins:
            c.update_spin_only()
            if c.can_collect():
                collector = None
                for p in players:
                    if p.health > 0 and self.check_collision(p, self.config.player_radius, c, self.config.coin_radius):
                        collector = p
                        break
                if collector:
                    self._collect_coin(collector, c)

        # Power-ups
        for pu in self.power_ups:
            pu.update(self._no_keys)
            for p in players:
                r = self.config.double_score_radius if isinstance(pu, DoubleScorePower) else self.config.invincible_radius
                if (self.check_collision(p, self.config.player_radius, pu, r)
                        and not pu.is_collected()):
                    pu.activate(p)
                    self._audio.play_sfx("powerup")

        # End flag (any player reaching wins)
        for f in self.end_flags:
            f.update(self._no_keys)
            for p in players:
                if (p.health > 0
                        and self.check_collision(p, self.config.player_radius, f, self.config.end_flag_radius)):
                    self.finalize_race_by_score()
                    return

        # Knockout exit detection (health depleted -> fall out of frame -> other player wins)
        for p in players:
            if p.health <= 0 and p.y > self.config.window_height + 40:
                winner = self.player2 if p is self.player else self.player
                self._set_race_winner(winner)
                self.is_win = True
                return

        # Fall detection (race mode has no respawn)
        for p in players:
            if p.y > self.config.window_height and p.health > 0:
                winner = self.player2 if p is self.player else self.player
                self._set_race_winner(winner)
                self.is_win = True
                return

    def _draw_race(self, screen, offset=(0, 0)):
        for p in self.platforms:
            p.draw(screen, offset)
        for e in self.enemies:
            e.draw(screen, offset)
        for c in self.coins:
            c.draw(screen, offset)
        for pu in self.power_ups:
            pu.draw(screen, offset)
        if self.boss is not None:
            self.boss.draw(screen, offset)
        for fb in self.fireballs:
            fb.draw(screen, offset)
        for f in self.end_flags:
            f.draw(screen, offset)
        if self.player is not None:
            self.player.draw(screen, offset)
        if self.player2 is not None:
            self.player2.draw(screen, offset)
        self.particles.draw(screen, camera_offset=(-offset[0], -offset[1]))

    def _draw_race_hud(self, screen):
        font = self.config.status_font

        # Top-left: P1 score
        p1_text = f"P1 SCORE {self.player.score}"
        p1_surf = font.render(p1_text, True, (255, 255, 255))
        p1_shadow = font.render(p1_text, True, (50, 50, 50))
        screen.blit(p1_shadow, (27, 22))
        screen.blit(p1_surf, (25, 20))

        # Top-right: P2 score
        p2_text = f"P2 SCORE {self.player2.score}"
        p2_surf = font.render(p2_text, True, (255, 100, 100))
        p2_shadow = font.render(p2_text, True, (50, 50, 50))
        p2_x = self.config.window_width - p2_surf.get_width() - 25
        screen.blit(p2_shadow, (p2_x + 2, 22))
        screen.blit(p2_surf, (p2_x, 20))
        self._draw_player_bars(
            screen,
            self.player,
            20,
            56,
            health_color=self.UNIFIED_HEALTH_BAR_COLOR,
            inv_color=self.UNIFIED_INV_BAR_COLOR,
            health_max=100.0,
        )
        self._draw_player_bars(
            screen,
            self.player2,
            self.config.window_width - 220,
            56,
            health_color=self.UNIFIED_HEALTH_BAR_COLOR,
            inv_color=self.UNIFIED_INV_BAR_COLOR,
            health_max=100.0,
        )

        # Center: time
        minutes = int(self.elapsed_time) // 60
        seconds = int(self.elapsed_time) % 60
        time_text = f"TIME {minutes:02d}:{seconds:02d}"
        time_surf = font.render(time_text, True, (255, 255, 255))
        time_x = self.config.window_width // 2 - time_surf.get_width() // 2
        screen.blit(time_surf, (time_x, 20))

    def _draw_player_bars(self, screen, player, x, y, health_color, inv_color, health_max):
        if player is None:
            return

        bar_w = 200
        bar_h = 10
        gap = 6

        # Health bar
        health_ratio = 0.0 if health_max <= 0 else max(0.0, min(1.0, player.health / health_max))
        bg = pygame.Rect(x, y, bar_w, bar_h)
        fg = pygame.Rect(x, y, int(bar_w * health_ratio), bar_h)
        pygame.draw.rect(screen, (25, 25, 30), bg, border_radius=3)
        if fg.width > 0:
            pygame.draw.rect(screen, health_color, fg, border_radius=3)
        pygame.draw.rect(screen, (210, 210, 210), bg, 1, border_radius=3)

        # Invincibility bar
        inv_ratio = 0.0
        if player.max_invincibility_frames > 0:
            inv_ratio = max(0.0, min(1.0, player.invincibility_frames / player.max_invincibility_frames))
        inv_bg = pygame.Rect(x, y + bar_h + gap, bar_w, bar_h)
        inv_fg = pygame.Rect(x, y + bar_h + gap, int(bar_w * inv_ratio), bar_h)
        pygame.draw.rect(screen, (25, 25, 30), inv_bg, border_radius=3)
        if inv_fg.width > 0:
            pygame.draw.rect(screen, inv_color, inv_fg, border_radius=3)
        pygame.draw.rect(screen, (210, 210, 210), inv_bg, 1, border_radius=3)
