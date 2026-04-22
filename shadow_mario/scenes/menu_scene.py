"""Main menu scene."""

import math
import random
from typing import List

import pygame

from shadow_mario.scene_payloads import LevelStartPayload
from .scene import Scene


class MenuScene(Scene):
    """Main menu scene, contains title animation, buttons and level selection."""

    BUTTON_WIDTH = 280
    BUTTON_HEIGHT = 50
    BUTTON_SPACING = 20

    def __init__(self, context) -> None:
        super().__init__(context)
        self.config = self.context.config
        self.rc = self.context.runtime_config
        self.save = self.context.save
        self._bg_image = pygame.image.load(self.config.background_image).convert()

        # Title animation
        self._title_time = 0.0
        self._title_base_y = self.config.title_y
        self._menu_particles: list[dict] = []
        for _ in range(36):
            self._spawn_particle(initial=True)

        # Button definitions
        self._buttons: list[dict] = []
        self._selected_index = 0
        self._build_buttons()

        # Level unlock status - read from save
        self._unlocked_levels: list[bool] = []
        self._high_scores: list[int] = []

    def _build_buttons(self) -> None:
        """Build menu button list."""
        cx = self.config.window_width // 2
        start_y = int(self.config.title_y + 180)

        labels = ["START GAME", "LEVEL SELECT", "SETTINGS", "QUIT"]
        actions = ["start_game", "level_select", "settings", "quit"]

        self._buttons = []
        for i, (label, action) in enumerate(zip(labels, actions)):
            y = start_y + i * (self.BUTTON_HEIGHT + self.BUTTON_SPACING)
            # Pre-calculate rect position so collision detection works immediately
            rect = pygame.Rect(0, 0, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
            rect.center = (cx, y)
            
            self._buttons.append({
                "label": label,
                "action": action,
                "rect": rect,
                "center": (cx, y),
            })

    def _refresh_save_data(self) -> None:
        """Read latest unlock status and high scores from save."""
        self._unlocked_levels = self.save.get_unlocked_levels()
        # Ensure at least 4 levels
        while len(self._unlocked_levels) < 4:
            self._unlocked_levels.append(False)
        self._high_scores = [
            self.save.get_high_score(1),
            self.save.get_high_score(2),
            self.save.get_high_score(3),
            self.save.get_high_score(4),
        ]

    def on_enter(self, data: dict | None = None) -> None:
        super().on_enter(data)
        self._title_time = 0.0
        self._selected_index = 0
        self._refresh_save_data()
        self.context.audio.play_bgm("bgm_menu")

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self._switch_to("quit")
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._switch_to("quit")
                    return
                elif event.key == pygame.K_UP:
                    self._selected_index = (self._selected_index - 1) % len(self._buttons)
                elif event.key == pygame.K_DOWN:
                    self._selected_index = (self._selected_index + 1) % len(self._buttons)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self._activate_button(self._selected_index)

                # Number keys for quick level select (from save)
                if event.key == pygame.K_1:
                    self._switch_to("loading", LevelStartPayload(level=1))
                elif event.key == pygame.K_2 and len(self._unlocked_levels) > 1 and self._unlocked_levels[1]:
                    self._switch_to("loading", LevelStartPayload(level=2))
                elif event.key == pygame.K_3 and len(self._unlocked_levels) > 2 and self._unlocked_levels[2]:
                    self._switch_to("loading", LevelStartPayload(level=3))
                elif event.key == pygame.K_4 and len(self._unlocked_levels) > 3 and self._unlocked_levels[3]:
                    self._switch_to("loading", LevelStartPayload(level=4))

            # Mouse support
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                for i, btn in enumerate(self._buttons):
                    if btn["rect"].collidepoint(mx, my):
                        self._selected_index = i

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for i, btn in enumerate(self._buttons):
                    if btn["rect"].collidepoint(mx, my):
                        self._activate_button(i)

    def _activate_button(self, index: int) -> None:
        """Activate the specified button."""
        action = self._buttons[index]["action"]
        if action == "start_game":
            # Start from first unlocked level, or level 1
            self._switch_to("loading", LevelStartPayload(level=1))
        elif action == "level_select":
            self._switch_to("level_select")
        elif action == "settings":
            self._switch_to("settings")
        elif action == "quit":
            self._switch_to("quit")

    def update(self, dt: float) -> None:
        self._title_time += dt
        self._update_particles(dt)

    def draw(self, screen: pygame.Surface) -> None:
        # Background
        screen.blit(self._bg_image, (0, 0))
        self._draw_particles(screen)

        # Title animation + subtle glow.
        title_y = self._title_base_y + math.sin(self._title_time * 1.9) * 7
        title_surf = self.config.title_font.render(
            self.config.msg_props.get("title", "SHADOW MARIO"),
            True,
            self.rc.color("text_primary"),
        )
        glow_surf = self.config.title_font.render(
            self.config.msg_props.get("title", "SHADOW MARIO"),
            True,
            (100, 160, 255),
        )
        glow_surf.set_alpha(70)
        title_rect = title_surf.get_rect(center=(self.config.window_width // 2, title_y))
        glow_rect = glow_surf.get_rect(center=(self.config.window_width // 2, title_y))
        screen.blit(glow_surf, (glow_rect.x - 2, glow_rect.y))
        screen.blit(glow_surf, (glow_rect.x + 2, glow_rect.y))
        screen.blit(title_surf, title_rect)

        # Buttons
        for i, btn in enumerate(self._buttons):
            is_selected = i == self._selected_index
            self._draw_button(screen, btn, is_selected)

        # High score display
        total_high = sum(self._high_scores) if self._high_scores else 0
        if total_high > 0:
            hs_text = f"BEST: {total_high}"
            hs_surf = self.config.instruction_font.render(hs_text, True, (255, 215, 0))
            screen.blit(hs_surf, (20, self.config.window_height - 30))

        # Total coins from save
        total_coins = self.save.get_total_coins()
        if total_coins > 0:
            coin_text = f"COINS: {total_coins}"
            coin_surf = self.config.instruction_font.render(coin_text, True, (255, 215, 0))
            screen.blit(coin_surf, (20, self.config.window_height - 55))

        # Version info
        version_surf = self.config.instruction_font.render("v1.1.0", True, self.rc.color("text_hint"))
        screen.blit(version_surf, (self.config.window_width - version_surf.get_width() - 20, self.config.window_height - 30))
        hint_text = "PRESS 1-4 TO QUICK START LEVEL"
        hint_surf = self.config.instruction_font.render(hint_text, True, self.rc.color("text_hint"))
        hint_rect = hint_surf.get_rect(center=(self.config.window_width // 2, self.config.window_height - 28))
        screen.blit(hint_surf, hint_rect)

    def _draw_button(self, screen: pygame.Surface, btn: dict, selected: bool) -> None:
        """Draw a single button."""
        rect = btn["rect"]

        bg_color = self.rc.color("button_bg_hover") if selected else self.rc.color("button_bg")
        border_color = self.rc.color("button_border_hover") if selected else self.rc.color("button_border")
        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(screen, border_color, rect, width=2, border_radius=8)

        # Simplified selected effect: subtle border highlight instead of glow
        if selected:
            pygame.draw.rect(screen, (100, 150, 255), rect, width=3, border_radius=8)

        # Text
        text_color = self.rc.color("text_primary") if selected else self.rc.color("text_secondary")
        label_surf = self.config.instruction_font.render(btn["label"], True, text_color)
        label_rect = label_surf.get_rect(center=rect.center)
        screen.blit(label_surf, label_rect)

    def _spawn_particle(self, initial: bool = False) -> None:
        x = random.uniform(0, self.config.window_width)
        if initial:
            y = random.uniform(0, self.config.window_height)
        else:
            y = self.config.window_height + random.uniform(0, 120)
        self._menu_particles.append({
            "x": x,
            "y": y,
            "r": random.uniform(1.2, 2.8),
            "speed": random.uniform(14, 40),
            "phase": random.uniform(0, math.pi * 2),
            "alpha": random.randint(55, 120),
        })

    def _update_particles(self, dt: float) -> None:
        while len(self._menu_particles) < 36:
            self._spawn_particle()
        for p in self._menu_particles:
            p["y"] -= p["speed"] * dt
            p["x"] += math.sin(self._title_time * 1.5 + p["phase"]) * 0.6
        self._menu_particles = [p for p in self._menu_particles if p["y"] > -24]

    def _draw_particles(self, screen: pygame.Surface) -> None:
        layer = pygame.Surface((self.config.window_width, self.config.window_height), pygame.SRCALPHA)
        for p in self._menu_particles:
            pygame.draw.circle(
                layer,
                (140, 190, 255, int(p["alpha"])),
                (int(p["x"]), int(p["y"])),
                int(p["r"]),
            )
        screen.blit(layer, (0, 0))
