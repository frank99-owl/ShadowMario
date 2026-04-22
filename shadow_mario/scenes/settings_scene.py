"""Settings scene."""

from typing import List

import pygame

from shadow_mario.config import GameConfig
from shadow_mario.audio import get_audio_manager
from shadow_mario.save import get_save_manager
from shadow_mario.ui_components import Slider
from .scene import Scene


class SettingsScene(Scene):
    """Settings interface with working volume controls and reset options."""

    BUTTON_WIDTH = 260
    BUTTON_HEIGHT = 45
    BUTTON_SPACING = 15

    def __init__(self) -> None:
        super().__init__()
        self.config = GameConfig()
        self.audio = get_audio_manager()
        self.save = get_save_manager()
        self._selected_index = 0  # 0=master, 1=bgm, 2=sfx, 3=mute, 4=reset, 5=back
        self._slider_selected = 0  # Which slider is selected for keyboard control

        # Sliders
        slider_width = 300
        slider_x = self.config.window_width // 2 - slider_width // 2
        start_y = self.config.window_height // 2 - 100

        self._master_slider = Slider(
            slider_x, start_y, slider_width, 20,
            label="MASTER VOLUME", initial_value=self.audio.master_volume
        )
        self._bgm_slider = Slider(
            slider_x, start_y + 60, slider_width, 20,
            label="BGM VOLUME", initial_value=self.audio.bgm_volume
        )
        self._sfx_slider = Slider(
            slider_x, start_y + 120, slider_width, 20,
            label="SFX VOLUME", initial_value=self.audio.sfx_volume
        )
        self._sliders = [self._master_slider, self._bgm_slider, self._sfx_slider]

        # Mute toggle button
        self._mute_rect = pygame.Rect(
            self.config.window_width // 2 - 90,
            start_y + 180,
            180, 45
        )

        # Reset button
        self._reset_rect = pygame.Rect(
            self.config.window_width // 2 - 120,
            start_y + 240,
            240, 45
        )

        # Back button
        self._back_rect = pygame.Rect(
            self.config.window_width // 2 - 80,
            self.config.window_height - 80,
            160, 45
        )

        self._overlay = pygame.Surface(
            (self.config.window_width, self.config.window_height), pygame.SRCALPHA
        )
        self._overlay.fill((0, 0, 0, 180))

    def on_enter(self, data: dict | None = None) -> None:
        super().on_enter(data)
        # Refresh slider values from current audio state
        self._master_slider.value = self.audio.master_volume
        self._bgm_slider.value = self.audio.bgm_volume
        self._sfx_slider.value = self.audio.sfx_volume

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self._switch_to("quit")
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._go_back()
                    return
                elif event.key == pygame.K_UP:
                    self._selected_index = max(0, self._selected_index - 1)
                    self._slider_selected = min(self._selected_index, 2)
                elif event.key == pygame.K_DOWN:
                    self._selected_index = min(5, self._selected_index + 1)
                    self._slider_selected = min(self._selected_index, 2)
                elif event.key == pygame.K_LEFT:
                    if self._selected_index <= 2:
                        # Adjust slider down
                        slider = self._sliders[self._selected_index]
                        slider.value = max(0.0, slider.value - 0.05)
                        self._apply_audio_settings()
                elif event.key == pygame.K_RIGHT:
                    if self._selected_index <= 2:
                        # Adjust slider up
                        slider = self._sliders[self._selected_index]
                        slider.value = min(1.0, slider.value + 0.05)
                        self._apply_audio_settings()
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self._selected_index == 3:
                        self.audio.toggle_mute()
                    elif self._selected_index == 4:
                        self._reset_all()
                    elif self._selected_index == 5:
                        self._go_back()

            # Slider interactions (mouse)
            for slider in self._sliders:
                if slider.handle_event(event):
                    self._apply_audio_settings()

            # Button clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if self._mute_rect.collidepoint(mx, my):
                    self.audio.toggle_mute()
                    self._selected_index = 3

                elif self._reset_rect.collidepoint(mx, my):
                    self._reset_all()
                    self._selected_index = 4

                elif self._back_rect.collidepoint(mx, my):
                    self._go_back()

    def _apply_audio_settings(self) -> None:
        """Apply slider values to audio manager."""
        self.audio.set_master_volume(self._master_slider.value)
        self.audio.set_bgm_volume(self._bgm_slider.value)
        self.audio.set_sfx_volume(self._sfx_slider.value)
        # Save settings
        self.save.set_audio_settings(self.audio.get_settings())

    def _reset_all(self) -> None:
        """Reset all settings to defaults."""
        self.audio.set_master_volume(1.0)
        self.audio.set_bgm_volume(0.7)
        self.audio.set_sfx_volume(0.8)
        self.save.set_audio_settings(self.audio.get_settings())
        # Update sliders
        self._master_slider.value = 1.0
        self._bgm_slider.value = 0.7
        self._sfx_slider.value = 0.8

    def _go_back(self) -> None:
        """Return to previous scene."""
        return_to = self._transition_data.get("return_to", "menu")
        if return_to == "pause":
            pause_data = self._transition_data.get("pause_data", {})
            self._switch_to("pause", pause_data)
        else:
            self._switch_to("menu")

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self._overlay, (0, 0))

        # Title
        title_surf = self.config.title_font.render("SETTINGS", True, (255, 255, 255))
        title_rect = title_surf.get_rect(
            center=(self.config.window_width // 2, 120)
        )
        screen.blit(title_surf, title_rect)

        # Keyboard hint
        hint_surf = self.config.instruction_font.render(
            "USE ARROW KEYS TO CHANGE - ENTER TO APPLY", True, (150, 150, 150)
        )
        screen.blit(hint_surf, hint_surf.get_rect(center=(self.config.window_width // 2, 160)))

        # Sliders with selection highlight
        for i, slider in enumerate(self._sliders):
            slider.draw(screen, self.config.instruction_font)
            if self._selected_index == i:
                # Draw highlight border around selected slider
                highlight = pygame.Surface((slider.width + 8, 50), pygame.SRCALPHA)
                pygame.draw.rect(highlight, (100, 150, 255, 60), highlight.get_rect(), border_radius=4)
                screen.blit(highlight, (slider.x - 4, slider.y - 25))

        # Mute button
        mute_text = "UNMUTE" if self.audio.is_muted() else "MUTE"
        mute_color = (200, 100, 100) if self.audio.is_muted() else (100, 100, 200)
        pygame.draw.rect(screen, mute_color, self._mute_rect, border_radius=6)
        border_color = (100, 150, 255) if self._selected_index == 3 else (200, 200, 200)
        pygame.draw.rect(screen, border_color, self._mute_rect, width=2, border_radius=6)
        mute_surf = self.config.instruction_font.render(mute_text, True, (255, 255, 255))
        screen.blit(mute_surf, mute_surf.get_rect(center=self._mute_rect.center))

        # Reset button
        pygame.draw.rect(screen, (200, 100, 100), self._reset_rect, border_radius=6)
        border_color = (100, 150, 255) if self._selected_index == 4 else (200, 200, 200)
        pygame.draw.rect(screen, border_color, self._reset_rect, width=2, border_radius=6)
        reset_surf = self.config.instruction_font.render("RESET ALL", True, (255, 255, 255))
        screen.blit(reset_surf, reset_surf.get_rect(center=self._reset_rect.center))

        # Back button
        pygame.draw.rect(screen, (60, 60, 100), self._back_rect, border_radius=6)
        border_color = (100, 150, 255) if self._selected_index == 5 else (100, 150, 255)
        pygame.draw.rect(screen, border_color, self._back_rect, width=2, border_radius=6)
        back_surf = self.config.instruction_font.render("BACK", True, (255, 255, 255))
        screen.blit(back_surf, back_surf.get_rect(center=self._back_rect.center))
