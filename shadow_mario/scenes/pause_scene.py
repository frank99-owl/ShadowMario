"""Pause scene (overlay)."""

from typing import List

import pygame

from shadow_mario.config import GameConfig
from .scene import Scene


class PauseScene(Scene):
    """Pause overlay scene, semi-transparent background + menu options."""

    BUTTON_WIDTH = 320
    BUTTON_HEIGHT = 45
    BUTTON_SPACING = 15

    def __init__(self) -> None:
        super().__init__()
        self.config = GameConfig()
        self._selected_index = 0
        self._buttons: list[dict] = []
        self._build_buttons()

        # Semi-transparent overlay
        self._overlay = pygame.Surface(
            (self.config.window_width, self.config.window_height), pygame.SRCALPHA
        )
        self._overlay.fill((0, 0, 0, 160))

    def _build_buttons(self) -> None:
        """Build pause menu buttons."""
        cx = self.config.window_width // 2
        start_y = self.config.window_height // 2 - 60

        labels = ["RESUME", "RESTART", "SETTINGS", "QUIT TO MENU"]
        actions = ["resume", "restart", "settings", "quit_to_menu"]

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

    def on_enter(self, data: dict | None = None) -> None:
        super().on_enter(data)
        self._selected_index = 0

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self._switch_to("quit")
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC to resume game
                    self._switch_to("resume")
                    return
                elif event.key == pygame.K_UP:
                    self._selected_index = (self._selected_index - 1) % len(self._buttons)
                elif event.key == pygame.K_DOWN:
                    self._selected_index = (self._selected_index + 1) % len(self._buttons)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self._activate_button(self._selected_index)

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
        """Activate button."""
        if not self._buttons:
            return
            
        action = self._buttons[index]["action"]
        data = self._transition_data

        if action == "resume":
            self._switch_to("resume")
        elif action == "restart":
            self._switch_to("game", {"level": data.get("level", 1)})
        elif action == "settings":
            self._switch_to("settings", {"return_to": "pause", "pause_data": data})
        elif action == "quit_to_menu":
            self._switch_to("menu")

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        # Semi-transparent overlay
        screen.blit(self._overlay, (0, 0))

        # Title
        title_surf = self.config.title_font.render("PAUSED", True, (255, 255, 255))
        title_rect = title_surf.get_rect(
            center=(self.config.window_width // 2, self.config.window_height // 2 - 130)
        )
        screen.blit(title_surf, title_rect)

        # Buttons
        for i, btn in enumerate(self._buttons):
            is_selected = i == self._selected_index
            self._draw_button(screen, btn, is_selected)

    def _draw_button(self, screen: pygame.Surface, btn: dict, selected: bool) -> None:
        """Draw button."""
        rect = btn["rect"]

        bg_color = (60, 60, 100) if selected else (40, 40, 60)
        border_color = (100, 150, 255) if selected else (60, 60, 80)
        pygame.draw.rect(screen, bg_color, rect, border_radius=6)
        pygame.draw.rect(screen, border_color, rect, width=2, border_radius=6)

        text_color = (255, 255, 255) if selected else (200, 200, 200)
        label_surf = self.config.instruction_font.render(btn["label"], True, text_color)
        label_rect = label_surf.get_rect(center=rect.center)
        screen.blit(label_surf, label_rect)
