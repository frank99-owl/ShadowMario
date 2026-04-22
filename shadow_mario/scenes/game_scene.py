"""Game scene, handles actual level gameplay."""

import random
from typing import List

import pygame

from shadow_mario.level import Level
from shadow_mario.scene_payloads import GameOverPayload, LevelStartPayload, SettingsRoutePayload
from shadow_mario.tutorial import TutorialHint, TutorialManager
from shadow_mario.transition import FadeTransition
from shadow_mario.entities.player import Player
from .scene import Scene


class GameScene(Scene):
    """Game scene responsible for level loading, updating, rendering and pause handling."""

    BUTTON_WIDTH = 260
    BUTTON_HEIGHT = 45
    BUTTON_SPACING = 15

    def __init__(self, context) -> None:
        super().__init__(context)
        self.config = self.context.config
        self._bg_image = pygame.image.load(self.config.background_image).convert()
        self._level: Level | None = None
        self._level_number = 1
        self._s_pressed_last = False
        self._paused = False
        self._pause_selected = 0
        self._pause_buttons: list[dict] = []
        self._build_pause_buttons()

        # Pause overlay
        self._pause_overlay = pygame.Surface(
            (self.config.window_width, self.config.window_height), pygame.SRCALPHA
        )
        self._pause_overlay.fill((0, 0, 0, 160))

        # Tutorial manager
        self._tutorial = TutorialManager()

        # Damage flash overlay
        self._damage_flash = 0.0

        # Transition
        self._transition = FadeTransition()
        self._transition_pending: dict | None = None

        # Speed lines effect
        self._speed_lines: list[dict] = []

        # Respawn flash effect
        self._respawn_flash = 0.0

        # Screenshot notification
        self._screenshot_notify_timer = 0.0
        self._screenshot_dir = self._ensure_screenshot_dir()

        # Camera zoom for race mode (level 4)
        self._zoom_scale = 1.0
        self._min_zoom = 0.35
        self._race_safe_border_x = 90
        self._race_safe_border_y = 70
        self._race_out_margin = 40
        self._race_camera_state: dict | None = None
        self._world_surface: pygame.Surface | None = None

    def _ensure_screenshot_dir(self) -> str:
        """Ensure screenshots directory exists."""
        import os
        ss_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "screenshots")
        os.makedirs(ss_dir, exist_ok=True)
        return ss_dir

    def _take_screenshot(self, screen: pygame.Surface) -> None:
        """Save current screen to screenshots directory."""
        import os
        from datetime import datetime
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self._screenshot_dir, filename)
        pygame.image.save(screen, filepath)
        self._screenshot_notify_timer = 2.0

    def _build_pause_buttons(self) -> None:
        """Build pause menu buttons."""
        cx = self.config.window_width // 2
        start_y = self.config.window_height // 2 - 60

        labels = ["RESUME", "RESTART", "SETTINGS", "QUIT TO MENU"]
        actions = ["resume", "restart", "settings", "quit_to_menu"]

        self._pause_buttons = []
        for i, (label, action) in enumerate(zip(labels, actions)):
            y = start_y + i * (self.BUTTON_HEIGHT + self.BUTTON_SPACING)
            self._pause_buttons.append({
                "label": label,
                "action": action,
                "rect": pygame.Rect(0, 0, self.BUTTON_WIDTH, self.BUTTON_HEIGHT),
                "center": (cx, y),
            })

    def _build_tutorial(self) -> None:
        """Build tutorial hints for first level."""
        cx = self.config.window_width // 2
        font = self.config.instruction_font

        if self._level_number == 4:
            # Place hints near bottom of screen, below platforms
            bottom_y = self.config.window_height - 60
            self._tutorial.add_hint(TutorialHint(
                "PLAYER 1: WASD to move. PLAYER 2: ARROWS to move.", cx, bottom_y, font,
                fade_in_duration=0.5, stay_duration=4.0, fade_out_duration=0.5
            ))
            self._tutorial.add_hint(TutorialHint(
                "Race to the flag! Collect the most coins to win!", cx, bottom_y, font,
                fade_in_duration=0.5, stay_duration=4.0, fade_out_duration=0.5
            ))
            self._tutorial.start()

    def _load_level(self, level_number: int) -> None:
        level_file = self._get_level_file(level_number)
        self._level = Level(level_file, self.config, level_number, audio_manager=self.context.audio)
        self._level.best_time = self.context.save.get_best_time(level_number)

    def on_enter(self, data: dict | None = None) -> None:
        super().on_enter(data)
        payload = LevelStartPayload.from_mapping(data)
        self._level_number = payload.level
        self._load_level(self._level_number)
        self._s_pressed_last = False
        self._paused = False
        self._pause_selected = 0
        self._damage_flash = 0.0
        self._transition_pending = None
        self._speed_lines = []
        self._respawn_flash = 0.0
        self._screenshot_notify_timer = 0.0
        self._race_camera_state = None
        self.context.audio.play_bgm("bgm_level")

        # Setup tutorial for level 1
        self._tutorial = TutorialManager()
        self._build_tutorial()

        # Fade in
        self._transition.start_fade_in(duration=0.4)

    def _get_level_file(self, level: int) -> str:
        """Get level file path based on level number."""
        mapping = {
            1: self.config.level1_file,
            2: self.config.level2_file,
            3: self.config.level3_file,
            4: self.config.level4_file,
        }
        return mapping.get(level, self.config.level1_file)

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        # Block input during transition
        if self._transition.is_active():
            return

        for event in events:
            if event.type == pygame.QUIT:
                self._switch_to("quit")
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._paused = not self._paused
                    self._pause_selected = 0
                    return

                # F12 screenshot
                if event.key == pygame.K_F12:
                    # Need to capture screen after drawing, set flag
                    self._screenshot_notify_timer = -1  # Special flag: take screenshot next frame
                    return

                if self._paused:
                    if event.key == pygame.K_UP:
                        self._pause_selected = (self._pause_selected - 1) % len(self._pause_buttons)
                    elif event.key == pygame.K_DOWN:
                        self._pause_selected = (self._pause_selected + 1) % len(self._pause_buttons)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self._activate_pause_button(self._pause_selected)

            if self._paused and event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                for i, btn in enumerate(self._pause_buttons):
                    if btn["rect"].collidepoint(mx, my):
                        self._pause_selected = i

            if self._paused and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for i, btn in enumerate(self._pause_buttons):
                    if btn["rect"].collidepoint(mx, my):
                        self._activate_pause_button(i)

    def _activate_pause_button(self, index: int) -> None:
        """Activate pause menu button."""
        action = self._pause_buttons[index]["action"]
        if action == "resume":
            self._paused = False
        elif action == "restart":
            self._paused = False
            self._load_level(self._level_number)
            self._s_pressed_last = False
            self._tutorial = TutorialManager()
            self._build_tutorial()
            self._race_camera_state = None
        elif action == "settings":
            self._switch_to(
                "settings",
                SettingsRoutePayload(return_to="game", level=self._level_number),
            )
        elif action == "quit_to_menu":
            self._start_transition_to("menu")

    def _start_transition_to(self, scene_name: str, data: dict | None = None) -> None:
        """Start fade out transition to another scene."""
        self._transition_pending = {"name": scene_name, "data": data or {}}
        self._transition.start_fade_out(duration=0.4, callback=self._on_fade_complete)

    def _on_fade_complete(self) -> None:
        """Called when fade out completes."""
        if self._transition_pending:
            name = self._transition_pending["name"]
            data = self._transition_pending["data"]
            self._transition_pending = None
            self._switch_to(name, data)

    def update(self, dt: float) -> None:
        # Always update transition
        self._transition.update(dt)

        if self._level is None or self._paused:
            return

        # Block updates during transition
        if self._transition.is_active():
            return

        keys = pygame.key.get_pressed()

        # S key shoots fireball (wasPressed)
        s_just_pressed = False
        if keys[pygame.K_s] and not self._s_pressed_last:
            s_just_pressed = True
        self._s_pressed_last = keys[pygame.K_s]

        self._level.update(keys, s_just_pressed)
        snapshot = self._level.snapshot()

        # Update zoom and check falling behind (race mode only)
        if self._level_number == 4 and snapshot.has_player2 and not snapshot.is_win and not snapshot.is_loss:
            self._update_zoom()
            loser = self._check_falling_behind()
            if loser:
                if loser is self._level.player:
                    self._level.force_race_winner(2)
                elif loser is self._level.player2:
                    self._level.force_race_winner(1)
                snapshot = self._level.snapshot()

        # Update tutorial
        self._tutorial.update(dt)

        # Update damage flash
        if self._damage_flash > 0:
            self._damage_flash -= dt * 3
            if self._damage_flash < 0:
                self._damage_flash = 0

        # Check for damage to trigger flash
        if self._level.player and snapshot.shake_intensity > 4:
            self._damage_flash = 0.5

        # Check for respawn to trigger flash effect
        if (self._level.player and self._level.player.respawn_effect_timer > 0
                and self._respawn_flash <= 0):
            self._respawn_flash = 0.6
            self.context.audio.play_sfx("powerup")

        # Update respawn flash
        if self._respawn_flash > 0:
            self._respawn_flash -= dt * 2
            if self._respawn_flash < 0:
                self._respawn_flash = 0

        # Update speed lines
        self._update_speed_lines(dt)

        # Update screenshot notification timer
        if self._screenshot_notify_timer > 0:
            self._screenshot_notify_timer -= dt

        # Check win
        if snapshot.is_win:
            result = self._level.build_result()
            self._start_transition_to("game_over", GameOverPayload(
                won=True,
                level=result.level,
                score=result.score,
                health=result.health,
                elapsed_time=result.elapsed_time,
                total_coins=result.total_coins,
                collected_coins=result.collected_coins,
                p1_score=result.p1_score,
                p2_score=result.p2_score,
                race_winner=result.race_winner,
            ))

        # Check loss (no lives left)
        if snapshot.is_loss:
            result = self._level.build_result()
            self._start_transition_to("game_over", GameOverPayload(
                won=False,
                level=result.level,
                score=result.score,
                health=result.health,
                elapsed_time=result.elapsed_time,
                total_coins=result.total_coins,
                collected_coins=result.collected_coins,
                p1_score=result.p1_score,
                p2_score=result.p2_score,
                race_winner=result.race_winner,
            ))

    def _update_speed_lines(self, dt: float) -> None:
        """Update speed line particles for fast movement feel."""
        if self._level is None or self._level.player is None:
            return

        keys = pygame.key.get_pressed()
        moving_fast = keys[pygame.K_RIGHT] or keys[pygame.K_LEFT]

        # Spawn speed lines when moving
        if moving_fast and random.random() < 0.3:
            self._speed_lines.append({
                "x": random.randint(0, self.config.window_width),
                "y": random.randint(0, self.config.window_height),
                "length": random.randint(30, 80),
                "speed": random.randint(200, 400),
                "alpha": random.randint(30, 80),
            })

        # Update existing lines
        i = 0
        direction = -1 if keys[pygame.K_RIGHT] else (1 if keys[pygame.K_LEFT] else 0)
        while i < len(self._speed_lines):
            line = self._speed_lines[i]
            line["x"] += line["speed"] * dt * direction
            line["alpha"] -= 50 * dt
            if line["alpha"] <= 0 or line["x"] < -100 or line["x"] > self.config.window_width + 100:
                self._speed_lines.pop(i)
            else:
                i += 1

    def draw(self, screen: pygame.Surface) -> None:
        # Draw game world (normal or camera mode)
        if self._level is not None and self._level.camera_mode:
            self._draw_camera_mode(screen)
        else:
            self._draw_normal_mode(screen)

        # Tutorial is drawn at native resolution (only in camera mode here;
        # normal mode draws it inside _draw_normal_mode)
        if self._level is not None and self._level.camera_mode:
            self._tutorial.draw(screen)

        # HUD is drawn at native resolution (not affected by zoom)
        if self._level is not None:
            self._level.draw_hud(screen)

        # Damage flash (full screen red tint when hurt)
        if self._damage_flash > 0:
            flash_surf = pygame.Surface((self.config.window_width, self.config.window_height), pygame.SRCALPHA)
            alpha = int(60 * self._damage_flash)
            flash_surf.fill((255, 0, 0, alpha))
            screen.blit(flash_surf, (0, 0))
            # Vignette red border for extra impact
            border_alpha = int(120 * self._damage_flash)
            pygame.draw.rect(flash_surf, (255, 0, 0, border_alpha), flash_surf.get_rect(), width=25)
            screen.blit(flash_surf, (0, 0))

        # Respawn flash effect (white flash + green particles feel)
        if self._respawn_flash > 0:
            flash_surf = pygame.Surface((self.config.window_width, self.config.window_height), pygame.SRCALPHA)
            alpha = int(120 * self._respawn_flash)
            flash_surf.fill((100, 255, 150, alpha))
            screen.blit(flash_surf, (0, 0))

            # "RESPAWN!" text without pulse
            respawn_text = self.config.title_font.render("RESPAWN", True, (100, 255, 150))
            respawn_rect = respawn_text.get_rect(
                center=(self.config.window_width // 2, self.config.window_height // 2)
            )
            screen.blit(respawn_text, respawn_rect)

        # Pause overlay
        if self._paused:
            screen.blit(self._pause_overlay, (0, 0))

            # Pause title
            title_surf = self.config.title_font.render("PAUSED", True, (255, 255, 255))
            title_rect = title_surf.get_rect(
                center=(self.config.window_width // 2, self.config.window_height // 2 - 130)
            )
            screen.blit(title_surf, title_rect)

            # Pause buttons
            for i, btn in enumerate(self._pause_buttons):
                is_selected = i == self._pause_selected
                self._draw_pause_button(screen, btn, is_selected)

            # Help text (moved up to avoid overlapping with tutorial hints)
            help_text = "ARROWS: Move | UP: Jump | S: Shoot | ESC: Pause"
            help_surf = self.config.instruction_font.render(help_text, True, (150, 150, 150))
            help_rect = help_surf.get_rect(
                center=(self.config.window_width // 2, self.config.window_height - 100)
            )
            screen.blit(help_surf, help_rect)

        # Transition overlay
        self._transition.draw(screen)

        # Screenshot: if flag is set, save the current frame
        if self._screenshot_notify_timer < 0:
            self._take_screenshot(screen)
            self._screenshot_notify_timer = 2.0

        # Screenshot saved notification
        if self._screenshot_notify_timer > 0:
            notify_alpha = int(255 * min(1.0, self._screenshot_notify_timer))
            notify_surf = self.config.instruction_font.render("Screenshot saved!", True, (100, 255, 150))
            notify_rect = notify_surf.get_rect(
                center=(self.config.window_width // 2, self.config.window_height - 80)
            )
            # Draw background pill
            pill_rect = notify_rect.inflate(20, 10)
            pill = pygame.Surface((pill_rect.width, pill_rect.height), pygame.SRCALPHA)
            pill.fill((20, 20, 30, min(200, notify_alpha)))
            screen.blit(pill, pill_rect)
            pygame.draw.rect(screen, (100, 255, 150, min(255, notify_alpha)), pill_rect, width=1, border_radius=4)
            screen.blit(notify_surf, notify_rect)

    def _draw_normal_mode(self, screen: pygame.Surface) -> None:
        """Draw game in normal mode (levels 1-3)."""
        # Calculate shake offset
        shake_x, shake_y = 0, 0
        if self._level is not None:
            snapshot = self._level.snapshot()
            if snapshot.shake_intensity > 0:
                shake_x = int(random.uniform(-snapshot.shake_intensity, snapshot.shake_intensity))
                shake_y = int(random.uniform(-snapshot.shake_intensity, snapshot.shake_intensity))

        # Draw everything to a temp surface, then apply shake
        if shake_x != 0 or shake_y != 0:
            temp = pygame.Surface((self.config.window_width, self.config.window_height))
            temp.blit(self._bg_image, (0, 0))
            if self._level is not None:
                self._level.draw(temp)
            # Speed lines
            self._draw_speed_lines(temp)
            # Tutorial
            self._tutorial.draw(temp)
            # Apply shake by blitting with offset
            screen.blit(temp, (shake_x, shake_y))
        else:
            screen.blit(self._bg_image, (0, 0))
            if self._level is not None:
                self._level.draw(screen)
            self._draw_speed_lines(screen)
            self._tutorial.draw(screen)

    def _draw_camera_mode(self, screen: pygame.Surface) -> None:
        """Draw game in camera mode with zoom (level 4 race mode)."""
        if self._level is None:
            self._draw_normal_mode(screen)
            return

        state = self._race_camera_state or self._compute_race_camera_state()
        if state is None:
            self._draw_normal_mode(screen)
            return

        cam_x = state["cam_x"]
        cam_y = state["cam_y"]
        viewport_w = state["viewport_w"]
        viewport_h = state["viewport_h"]
        self._zoom_scale = state["zoom"]
        self._race_camera_state = state

        # Create/reuse offscreen surface (SRCALPHA required for correct blitting)
        vw, vh = int(viewport_w), int(viewport_h)
        if self._world_surface is None or self._world_surface.get_size() != (vw, vh):
            self._world_surface = pygame.Surface((vw, vh), pygame.SRCALPHA)

        # Draw background (tiled)
        bg_w, bg_h = self._bg_image.get_size()
        offset_x = int(-cam_x) % bg_w - bg_w
        offset_y = int(-cam_y) % bg_h - bg_h
        for bx in range(offset_x, vw + bg_w, bg_w):
            for by in range(offset_y, vh + bg_h, bg_h):
                self._world_surface.blit(self._bg_image, (bx, by))

        # Apply screen shake
        shake_x, shake_y = 0, 0
        snapshot = self._level.snapshot()
        if snapshot.shake_intensity > 0:
            shake_x = int(random.uniform(-snapshot.shake_intensity, snapshot.shake_intensity))
            shake_y = int(random.uniform(-snapshot.shake_intensity, snapshot.shake_intensity))

        # Draw all entities with camera offset
        camera_offset = (-cam_x + shake_x, -cam_y + shake_y)
        self._level.draw(self._world_surface, offset=camera_offset)

        # Speed lines in camera space
        # (Skip for now - speed lines need adaptation for camera mode)

        scaled = pygame.transform.scale(self._world_surface,
                                        (self.config.window_width, self.config.window_height))
        screen.blit(scaled, (0, 0))

    def _update_zoom(self) -> None:
        """Update zoom and cache camera state for race mode."""
        state = self._compute_race_camera_state()
        self._race_camera_state = state
        self._zoom_scale = state["zoom"] if state else 1.0

    def _compute_race_camera_state(self):
        if self._level is None or self._level.player is None or self._level.player2 is None:
            return None

        p1, p2 = self._level.player, self._level.player2

        dx = abs(p1.x - p2.x)
        dy = abs(p1.y - p2.y)
        usable_w = max(1.0, self.config.window_width - self._race_safe_border_x * 2)
        usable_h = max(1.0, self.config.window_height - self._race_safe_border_y * 2)
        zoom_x = 1.0 if dx <= usable_w else usable_w / dx
        zoom_y = 1.0 if dy <= usable_h else usable_h / dy
        target_zoom = min(1.0, zoom_x, zoom_y)
        zoom = max(self._min_zoom, target_zoom)

        viewport_w = self.config.window_width / zoom
        viewport_h = self.config.window_height / zoom
        center_x = (p1.x + p2.x) / 2
        center_y = (p1.y + p2.y) / 2
        cam_x = center_x - viewport_w / 2

        # Keep players visible vertically while preferring a ground-biased framing.
        ground_cam_y = 745 - viewport_h * 0.78
        high_y = min(p1.y, p2.y)
        low_y = max(p1.y, p2.y)
        min_cam_y = low_y - (self.config.window_height - self._race_safe_border_y) / zoom
        max_cam_y = high_y - self._race_safe_border_y / zoom
        if min_cam_y <= max_cam_y:
            cam_y = min(max(ground_cam_y, min_cam_y), max_cam_y)
        else:
            cam_y = center_y - viewport_h / 2

        return {
            "cam_x": cam_x,
            "cam_y": cam_y,
            "viewport_w": viewport_w,
            "viewport_h": viewport_h,
            "zoom": zoom,
        }

    def _check_falling_behind(self):
        """Return the trailing player if they are fully out of the camera bounds."""
        if self._level is None or self._level.player is None or self._level.player2 is None:
            return None
        state = self._race_camera_state or self._compute_race_camera_state()
        if state is None:
            return None

        p1, p2 = self._level.player, self._level.player2
        cam_x = state["cam_x"]
        cam_y = state["cam_y"]
        zoom = state["zoom"]

        # Determine who's behind (lower x = behind in race mode)
        behind = p1 if p1.x <= p2.x else p2
        bx = (behind.x - cam_x) * zoom
        by = (behind.y - cam_y) * zoom

        if behind.health <= 0:
            return None

        if (bx < -self._race_out_margin
                or bx > self.config.window_width + self._race_out_margin
                or by < -self._race_out_margin
                or by > self.config.window_height + self._race_out_margin):
            return behind

        return None

    def _draw_speed_lines(self, screen: pygame.Surface) -> None:
        """Draw speed lines for fast movement effect."""
        for line in self._speed_lines:
            color = (255, 255, 255, int(line["alpha"]))
            start_pos = (int(line["x"]), int(line["y"]))
            # Draw with alpha using a small surface
            surf = pygame.Surface((line["length"], 2), pygame.SRCALPHA)
            pygame.draw.line(surf, color, (0, 1), (line["length"], 1), 1)
            screen.blit(surf, start_pos)

    def _draw_pause_button(self, screen: pygame.Surface, btn: dict, selected: bool) -> None:
        """Draw pause menu button."""
        rect = btn["rect"]
        rect.center = btn["center"]

        bg_color = (60, 60, 100) if selected else (40, 40, 60)
        border_color = (100, 150, 255) if selected else (60, 60, 80)
        pygame.draw.rect(screen, bg_color, rect, border_radius=6)
        pygame.draw.rect(screen, border_color, rect, width=2, border_radius=6)

        text_color = (255, 255, 255) if selected else (200, 200, 200)
        label_surf = self.config.instruction_font.render(btn["label"], True, text_color)
        label_rect = label_surf.get_rect(center=rect.center)
        screen.blit(label_surf, label_rect)

    def _draw_pause_stats(self, screen: pygame.Surface) -> None:
        """Draw statistics panel on pause screen."""
        if self._level is None or self._level.player is None:
            return
        snapshot = self._level.snapshot()

        # Right-aligned panel
        panel_w = 320
        panel_h = 200
        panel_x = self.config.window_width - panel_w - 40
        panel_y = 160

        # Semi-transparent panel background
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((20, 20, 30, 200))
        screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(screen, (60, 60, 80), (panel_x, panel_y, panel_w, panel_h), width=1, border_radius=4)

        # Stats title
        title = self.config.instruction_font.render("STATS", True, (255, 255, 255))
        screen.blit(title, (panel_x + 10, panel_y + 8))

        # Stats lines
        stats = [
            (f"SCORE {snapshot.score}", (255, 255, 255)),
            (f"LIVES {self._level.player.lives} OF {Player.MAX_LIVES}", (255, 50, 80)),
            (f"HEALTH {int(snapshot.health * 100)}", (100, 255, 100)),
            (f"COINS {snapshot.collected_coins} OF {snapshot.total_coins}", (255, 215, 0)),
            (f"COMBO X{snapshot.combo_count}", (255, 215, 0) if snapshot.combo_count > 1 else (200, 200, 200)),
        ]
        minutes = int(snapshot.elapsed_time) // 60
        seconds = int(snapshot.elapsed_time) % 60
        stats.append((f"TIME {minutes:02d} {seconds:02d}", (200, 200, 200)))

        if snapshot.checkpoint_count > 0:
            cp_text = f"CHECKPOINTS {snapshot.current_checkpoint_idx + 1} OF {snapshot.checkpoint_count}"
            stats.append((cp_text, (100, 255, 150)))

        line_y = panel_y + 35
        for text, color in stats:
            surf = self.config.instruction_font.render(text, True, color)
            screen.blit(surf, (panel_x + 12, line_y))
            line_y += 24
