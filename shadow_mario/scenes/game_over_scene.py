"""Game over scene (victory/defeat settlement)."""

import math
from typing import List

import pygame

from shadow_mario.config import GameConfig
from shadow_mario.save import get_save_manager
from shadow_mario.audio import get_audio_manager
from shadow_mario.achievements import get_achievement_manager
from .scene import Scene


class GameOverScene(Scene):
    """Settlement screen, displays victory/defeat info and statistics."""

    BUTTON_WIDTH = 320
    BUTTON_HEIGHT = 45
    BUTTON_SPACING = 15

    def __init__(self) -> None:
        super().__init__()
        self.config = GameConfig()
        self._won = False
        self._score = 0
        self._health = 0.0
        self._level = 1
        self._time = 0.0
        self._elapsed_time = 0.0
        self._total_coins = 0
        self._collected_coins = 0
        self._p1_score = 0
        self._p2_score = 0
        self._race_winner: int | None = None
        self._rank = ""
        self._selected_index = 0
        self._buttons: list[dict] = []
        self._high_score_beaten = False
        self._new_achievements: list[str] = []

        self._overlay = pygame.Surface(
            (self.config.window_width, self.config.window_height), pygame.SRCALPHA
        )
        self._overlay.fill((0, 0, 0, 180))

    def _calculate_rank(self) -> str:
        """Calculate S/A/B/C/D rank based on performance."""
        if not self._won:
            return "F"

        score = 0
        # Time bonus: under 60s = 3 pts, under 120s = 2 pts, under 180s = 1 pt
        if self._elapsed_time < 60:
            score += 3
        elif self._elapsed_time < 120:
            score += 2
        elif self._elapsed_time < 180:
            score += 1

        # Health bonus: full health = 2 pts, above 50% = 1 pt
        if self._health >= 1.0:
            score += 2
        elif self._health >= 0.5:
            score += 1

        # Coin bonus: all coins = 2 pts, above 75% = 1 pt
        if self._total_coins > 0:
            coin_ratio = self._collected_coins / self._total_coins
            if coin_ratio >= 1.0:
                score += 2
            elif coin_ratio >= 0.75:
                score += 1

        if score >= 6:
            return "S"
        elif score >= 4:
            return "A"
        elif score >= 2:
            return "B"
        elif score >= 1:
            return "C"
        return "D"

    def on_enter(self, data: dict | None = None) -> None:
        super().on_enter(data)
        d = data or {}
        self._won = d.get("won", False)
        self._score = d.get("score", 0)
        self._health = d.get("health", 0.0)
        self._level = d.get("level", 1)
        self._elapsed_time = d.get("elapsed_time", 0.0)
        self._total_coins = d.get("total_coins", 0)
        self._collected_coins = d.get("collected_coins", 0)
        self._p1_score = d.get("p1_score", 0)
        self._p2_score = d.get("p2_score", 0)
        self._race_winner = d.get("race_winner")
        self._time = 0.0
        self._selected_index = 0
        self._rank = self._calculate_rank()

        # Save: save high score + unlock next level + achievements + sound effects
        save = get_save_manager()
        audio = get_audio_manager()
        self._new_achievements = []
        if self._won:
            self._high_score_beaten = save.set_high_score(self._level, self._score)
            save.set_best_time(self._level, self._elapsed_time)
            if self._level < 4:
                save.unlock_level(self._level + 1)
            # Save coins
            save.add_coins(self._collected_coins)
            # Check achievements
            am = get_achievement_manager()
            self._new_achievements = am.check_level_complete(
                self._level, self._score, self._health, self._collected_coins
            )
            audio.stop_bgm(fade_ms=200)
            audio.play_sfx("win")
        else:
            audio.stop_bgm(fade_ms=200)
            audio.play_sfx("lose")

        self._build_buttons()

    def _build_buttons(self, start_y: int | None = None) -> None:
        """Build settlement screen buttons."""
        cx = self.config.window_width // 2
        if start_y is None:
            start_y = self.config.window_height // 2 + 60

        if self._won and self._level < 4:
            labels = ["NEXT LEVEL", "RETRY", "MAIN MENU"]
            actions = ["next_level", "retry", "menu"]
        else:
            labels = ["RETRY", "MAIN MENU"]
            actions = ["retry", "menu"]

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

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self._switch_to("quit")
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._switch_to("menu")
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
        if action == "next_level":
            self._switch_to("game", {"level": self._level + 1})
        elif action == "retry":
            self._switch_to("game", {"level": self._level})
        elif action == "menu":
            self._switch_to("menu")

    def update(self, dt: float) -> None:
        self._time += dt

    def draw(self, screen: pygame.Surface) -> None:
        # Semi-transparent overlay
        screen.blit(self._overlay, (0, 0))

        cx = self.config.window_width // 2
        current_y = 120  # Start below top edge

        # Title
        if self._won:
            title = "VICTORY!"
            title_color = (255, 215, 0)
        else:
            title = "GAME OVER"
            title_color = (255, 60, 60)

        # Removed float animation to reduce "fancy" layout as requested
        title_surf = self.config.title_font.render(title, True, title_color)
        title_rect = title_surf.get_rect(center=(cx, current_y))
        screen.blit(title_surf, title_rect)
        current_y += title_surf.get_height() + 15

        # Rank / Winner display
        if self._won:
            if self._level == 4:
                # Race mode: show winner in large font where rank used to be
                if self._race_winner in (1, 2):
                    winner = f"P{self._race_winner}"
                elif self._p1_score > self._p2_score:
                    winner = "P1"
                elif self._p2_score > self._p1_score:
                    winner = "P2"
                else:
                    winner = "TIE"
                winner_color = (255, 215, 0) if winner != "TIE" else (100, 255, 100)
                winner_surf = self.config.title_font.render(f"WINNER {winner}", True, winner_color)
                winner_rect = winner_surf.get_rect(center=(cx, current_y))
                screen.blit(winner_surf, winner_rect)
                current_y += winner_surf.get_height() + 20
            else:
                rank_colors = {
                    "S": (255, 215, 0), "A": (100, 255, 100),
                    "B": (100, 150, 255), "C": (200, 200, 200),
                    "D": (150, 100, 100), "F": (100, 100, 100),
                }
                rank_color = rank_colors.get(self._rank, (255, 255, 255))
                rank_surf = self.config.title_font.render(f"RANK {self._rank}", True, rank_color)
                rank_rect = rank_surf.get_rect(center=(cx, current_y))
                screen.blit(rank_surf, rank_rect)
                current_y += rank_surf.get_height() + 20

        # Stats info
        stats = []
        if self._level == 4:
            # Race mode: show both player scores
            stats.append(f"P1 SCORE {self._p1_score}")
            stats.append(f"P2 SCORE {self._p2_score}")
        else:
            stats.append(f"LEVEL {self._level}")
            stats.append(f"SCORE {self._score}")
        if self._won and self._level != 4:
            stats.append(f"HEALTH {int(self._health * 100)}")
            minutes = int(self._elapsed_time) // 60
            seconds = int(self._elapsed_time) % 60
            stats.append(f"TIME {minutes:02d} {seconds:02d}")
            if self._total_coins > 0:
                stats.append(f"COINS {self._collected_coins} OF {self._total_coins}")
                if self._collected_coins == self._total_coins:
                    stats.append("PERFECT ALL COINS")

        for stat in stats:
            stat_color = (255, 215, 0) if "PERFECT" in stat else (220, 220, 220)
            surf = self.config.instruction_font.render(stat, True, stat_color)
            rect = surf.get_rect(center=(cx, current_y))
            screen.blit(surf, rect)
            current_y += 28

        current_y += 20  # gap before buttons

        # Rebuild buttons at correct Y to avoid overlap
        self._build_buttons(int(current_y))

        # Buttons
        for i, btn in enumerate(self._buttons):
            is_selected = i == self._selected_index
            self._draw_button(screen, btn, is_selected)

        # Achievement unlock notifications (below buttons)
        if self._new_achievements:
            am = get_achievement_manager()
            ach_y = current_y + len(self._buttons) * (self.BUTTON_HEIGHT + self.BUTTON_SPACING) + 10
            for ach_id in self._new_achievements:
                ach = am.achievements.get(ach_id)
                if ach:
                    ach_text = f"ACHIEVEMENT UNLOCKED {ach.name}"
                    ach_surf = self.config.instruction_font.render(ach_text, True, (255, 215, 0))
                    ach_rect = ach_surf.get_rect(center=(cx, ach_y))
                    screen.blit(ach_surf, ach_rect)
                    ach_y += 24

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
