"""Loading scene, shown between menu and game."""

import math
import random
from typing import List

import pygame

from shadow_mario.config import GameConfig
from shadow_mario.audio import get_audio_manager
from .scene import Scene


class LoadingScene(Scene):
    """Loading screen with progress bar animation and gameplay tips."""

    LOADING_DURATION = 1.5  # Seconds to show loading screen

    TIPS = [
        "Press UP to jump - hold longer for higher jumps!",
        "Collect coins in a row to build combos and earn more points!",
        "Avoid enemies - they have a damage cooldown after hitting you.",
        "Press S to shoot fireballs when near the boss!",
        "Power-ups give temporary invincibility or double score!",
        "Checkpoints save your progress - reach them to respawn there!",
        "Collect all coins for a perfect bonus at the end!",
        "The faster you finish, the higher your time bonus!",
        "You have 3 lives - use them wisely!",
        "Flying platforms move horizontally - time your jumps!",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = GameConfig()
        self._bg_image = pygame.image.load(self.config.background_image).convert()
        self._time = 0.0
        self._progress = 0.0
        self._level = 1
        self._tip = ""
        self._tip_time = 0.0

        # Level names
        self._level_names = ["BEGINNER", "SKY HIGH", "BOSS BATTLE", "SHADOW RUN"]

    def on_enter(self, data: dict | None = None) -> None:
        super().on_enter(data)
        d = data or {}
        self._level = d.get("level", 1)
        self._time = 0.0
        self._progress = 0.0
        self._tip = random.choice(self.TIPS)
        self._tip_time = 0.0
        # Fade out menu BGM
        get_audio_manager().stop_bgm(fade_ms=300)

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        """Loading scene ignores all input events."""
        for event in events:
            if event.type == pygame.QUIT:
                self._switch_to("quit")
                return

    def update(self, dt: float) -> None:
        self._time += dt
        self._tip_time += dt

        # Fake loading progress (eases out)
        target = min(1.0, self._time / self.LOADING_DURATION)
        self._progress += (target - self._progress) * 0.1

        # Auto-switch to game when loading complete
        if self._time >= self.LOADING_DURATION:
            self._switch_to("game", {"level": self._level})

    def draw(self, screen: pygame.Surface) -> None:
        # Background
        screen.blit(self._bg_image, (0, 0))

        # Dark overlay
        overlay = pygame.Surface(
            (self.config.window_width, self.config.window_height), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        cx = self.config.window_width // 2

        # "LOADING" title with pulse
        pulse = 1.0 + 0.05 * math.sin(self._time * 8)
        title_surf = self.config.title_font.render("LOADING", True, (255, 255, 255))
        scaled = pygame.transform.scale(title_surf, (
            int(title_surf.get_width() * pulse),
            int(title_surf.get_height() * pulse)
        ))
        title_rect = scaled.get_rect(center=(cx, self.config.window_height // 2 - 80))
        screen.blit(scaled, title_rect)

        # Level name
        level_idx = min(self._level - 1, len(self._level_names) - 1)
        level_name = f"LEVEL {self._level} - {self._level_names[level_idx]}"
        name_surf = self.config.instruction_font.render(level_name, True, (200, 200, 200))
        name_rect = name_surf.get_rect(center=(cx, self.config.window_height // 2 - 20))
        screen.blit(name_surf, name_rect)

        # Progress bar
        bar_width = 300
        bar_height = 12
        bar_x = cx - bar_width // 2
        bar_y = self.config.window_height // 2 + 20

        # Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (40, 40, 40), bg_rect, border_radius=6)

        # Fill with gradient
        fill_width = int(bar_width * self._progress)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            # Gradient from blue to cyan
            r = int(100 + 100 * self._progress)
            g = int(150 + 105 * self._progress)
            b = int(255)
            pygame.draw.rect(screen, (r, g, b), fill_rect, border_radius=6)

        # Border
        pygame.draw.rect(screen, (100, 150, 255), bg_rect, width=1, border_radius=6)

        # Percentage
        pct_text = f"{int(self._progress * 100)}%"
        pct_surf = self.config.instruction_font.render(pct_text, True, (200, 200, 200))
        pct_rect = pct_surf.get_rect(center=(cx, bar_y + bar_height + 20))
        screen.blit(pct_surf, pct_rect)

        # Gameplay tip (typewriter effect)
        tip_y = self.config.window_height // 2 + 140
        tip_label = self.config.instruction_font.render("TIP:", True, (255, 215, 0))
        screen.blit(tip_label, (cx - tip_label.get_width() // 2, tip_y))

        # Typewriter: show characters progressively
        chars_to_show = min(len(self._tip), int(self._tip_time * 30))
        visible_tip = self._tip[:chars_to_show]
        tip_surf = self.config.instruction_font.render(visible_tip, True, (180, 180, 180))
        # Word wrap: wrap tip text to fit screen
        max_width = self.config.window_width - 100
        words = visible_tip.split(" ")
        lines = []
        current_line = ""
        for word in words:
            test = current_line + " " + word if current_line else word
            test_surf = self.config.instruction_font.render(test, True, (180, 180, 180))
            if test_surf.get_width() <= max_width:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        if not lines:
            lines = [visible_tip]

        line_y = tip_y + 35
        for line in lines:
            line_surf = self.config.instruction_font.render(line, True, (180, 180, 180))
            line_rect = line_surf.get_rect(center=(cx, line_y))
            screen.blit(line_surf, line_rect)
            line_y += 26
