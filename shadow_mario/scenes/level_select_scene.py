"""Level select scene."""

from typing import List

import pygame

from shadow_mario.scene_payloads import LevelStartPayload
from .scene import Scene


class LevelSelectScene(Scene):
    """Level selection interface showing level cards."""

    CARD_WIDTH = 235
    CARD_HEIGHT = 170
    CARD_SPACING = 15

    def __init__(self, context) -> None:
        super().__init__(context)
        self.config = self.context.config
        self.save = self.context.save
        self._bg_image = pygame.image.load(self.config.background_image).convert()
        self._selected_index = 0
        self._unlocked: list[bool] = []
        self._high_scores: list[int] = []
        self._time = 0.0

    def on_enter(self, data: dict | None = None) -> None:
        super().on_enter(data)
        self._selected_index = 0
        self._time = 0.0
        # Read unlock status and high scores from save
        self._unlocked = self.save.get_unlocked_levels()
        # Ensure at least 4 levels of data
        while len(self._unlocked) < 4:
            self._unlocked.append(False)
        self._high_scores = [
            self.save.get_high_score(1),
            self.save.get_high_score(2),
            self.save.get_high_score(3),
            self.save.get_high_score(4),
        ]

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self._switch_to("quit")
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._switch_to("menu")
                    return
                elif event.key == pygame.K_LEFT:
                    self._selected_index = max(0, self._selected_index - 1)
                elif event.key == pygame.K_RIGHT:
                    self._selected_index = min(3, self._selected_index + 1)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self._start_level(self._selected_index)
                elif event.key == pygame.K_1:
                    self._start_level(0)
                elif event.key == pygame.K_2 and self._unlocked[1]:
                    self._start_level(1)
                elif event.key == pygame.K_3 and self._unlocked[2]:
                    self._start_level(2)
                elif event.key == pygame.K_4 and self._unlocked[3]:
                    self._start_level(3)

            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                for i in range(4):
                    card_rect = self._get_card_rect(i)
                    if card_rect.collidepoint(mx, my):
                        self._selected_index = i

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for i in range(4):
                    card_rect = self._get_card_rect(i)
                    if card_rect.collidepoint(mx, my) and self._unlocked[i]:
                        self._start_level(i)

                # Back button
                back_rect = self._get_back_button_rect()
                if back_rect.collidepoint(mx, my):
                    self._switch_to("menu")

    def _start_level(self, index: int) -> None:
        """Start selected level."""
        if not self._unlocked[index]:
            return
        self._switch_to("loading", LevelStartPayload(level=index + 1))

    def _get_card_rect(self, index: int) -> pygame.Rect:
        """Get level card position."""
        # We have 4 levels now, so total width calculation should reflect that
        total_width = 4 * self.CARD_WIDTH + 3 * self.CARD_SPACING
        start_x = (self.config.window_width - total_width) // 2
        x = start_x + index * (self.CARD_WIDTH + self.CARD_SPACING)
        y = self.config.window_height // 2 - self.CARD_HEIGHT // 2
        return pygame.Rect(x, y, self.CARD_WIDTH, self.CARD_HEIGHT)

    def _get_back_button_rect(self) -> pygame.Rect:
        """Get back button position."""
        return pygame.Rect(
            self.config.window_width // 2 - 60,
            self.config.window_height - 80,
            120,
            40,
        )

    def update(self, dt: float) -> None:
        self._time += dt

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self._bg_image, (0, 0))

        # Title (simplified, no float)
        title_surf = self.config.title_font.render("SELECT LEVEL", True, (255, 255, 255))
        title_rect = title_surf.get_rect(
            center=(self.config.window_width // 2, self.config.title_y - 60)
        )
        screen.blit(title_surf, title_rect)

        # Level cards
        for i in range(4):
            self._draw_level_card(screen, i)

        # Back button
        self._draw_back_button(screen)

    def _draw_level_card(self, screen: pygame.Surface, index: int) -> None:
        """Draw a single level card."""
        rect = self._get_card_rect(index)
        is_selected = index == self._selected_index
        is_unlocked = self._unlocked[index]

        # Card background
        if is_unlocked:
            bg_color = (50, 50, 80) if not is_selected else (70, 70, 120)
            border_color = (100, 150, 255) if is_selected else (80, 80, 120)
        else:
            bg_color = (40, 40, 50)
            border_color = (60, 60, 70)

        pygame.draw.rect(screen, bg_color, rect, border_radius=10)
        pygame.draw.rect(screen, border_color, rect, width=2, border_radius=10)

        # Simplified selected effect: thicker border instead of glow
        if is_selected and is_unlocked:
            pygame.draw.rect(screen, (100, 150, 255), rect, width=4, border_radius=10)

        # Level number
        level_num = self.config.title_font.render(str(index + 1), True,
                                                   (255, 255, 255) if is_unlocked else (100, 100, 100))
        num_rect = level_num.get_rect(center=(rect.centerx, rect.centery - 15))
        screen.blit(level_num, num_rect)

        # Level name
        names = ["BEGINNER", "SKY HIGH", "BOSS BATTLE", "SHADOW RUN"]
        name_surf = self.config.instruction_font.render(names[index], True,
                                                         (200, 200, 200) if is_unlocked else (80, 80, 80))
        if name_surf.get_width() > rect.width - 20:
            scale_factor = (rect.width - 20) / name_surf.get_width()
            name_surf = pygame.transform.scale(name_surf, (int(name_surf.get_width() * scale_factor), int(name_surf.get_height() * scale_factor)))
        
        name_rect = name_surf.get_rect(center=(rect.centerx, rect.centery + 25))
        screen.blit(name_surf, name_rect)

        # High score display
        if is_unlocked:
            score_text = f"BEST {self._high_scores[index]}"
            score_surf = self.config.instruction_font.render(score_text, True, (180, 180, 150))
            if score_surf.get_width() > rect.width - 20:
                scale_factor = (rect.width - 20) / score_surf.get_width()
                score_surf = pygame.transform.scale(score_surf, (int(score_surf.get_width() * scale_factor), int(score_surf.get_height() * scale_factor)))
            score_rect = score_surf.get_rect(center=(rect.centerx, rect.bottom - 20))
            screen.blit(score_surf, score_rect)

        # Lock icon
        if not is_unlocked:
            lock_text = "LOCKED"
            lock_surf = self.config.instruction_font.render(lock_text, True, (150, 150, 150))
            lock_rect = lock_surf.get_rect(center=rect.center)
            screen.blit(lock_surf, lock_rect)

    def _draw_back_button(self, screen: pygame.Surface) -> None:
        """Draw back button."""
        rect = self._get_back_button_rect()

        pygame.draw.rect(screen, (60, 60, 100), rect, border_radius=6)
        pygame.draw.rect(screen, (100, 150, 255), rect, width=2, border_radius=6)

        text_surf = self.config.instruction_font.render("BACK", True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
