"""Tutorial hint system for new players."""

import pygame


class TutorialHint:
    """A single tutorial hint that fades in, stays visible, then fades out."""

    def __init__(
        self,
        text: str,
        x: float,
        y: float,
        font: pygame.font.Font,
        fade_in_duration: float = 0.5,
        stay_duration: float = 3.0,
        fade_out_duration: float = 0.5,
    ) -> None:
        self.text = text
        self.x = x
        self.y = y
        self.font = font
        self.fade_in_duration = fade_in_duration
        self.stay_duration = stay_duration
        self.fade_out_duration = fade_out_duration

        self._time = 0.0
        self._alpha = 0
        self._done = False

        # Pre-render text
        self._text_surf = font.render(text, True, (255, 255, 255))
        self._bg_surf = pygame.Surface(
            (self._text_surf.get_width() + 20, self._text_surf.get_height() + 12), pygame.SRCALPHA
        )
        pygame.draw.rect(self._bg_surf, (0, 0, 0, 180), self._bg_surf.get_rect(), border_radius=8)

    def update(self, dt: float) -> None:
        if self._done:
            return

        self._time += dt

        if self._time < self.fade_in_duration:
            self._alpha = int(255 * (self._time / self.fade_in_duration))
        elif self._time < self.fade_in_duration + self.stay_duration:
            self._alpha = 255
        elif self._time < self.fade_in_duration + self.stay_duration + self.fade_out_duration:
            progress = (self._time - self.fade_in_duration - self.stay_duration) / self.fade_out_duration
            self._alpha = int(255 * (1 - progress))
        else:
            self._alpha = 0
            self._done = True

    def draw(self, screen: pygame.Surface) -> None:
        if self._alpha <= 0:
            return

        # Draw background
        bg = self._bg_surf.copy()
        bg.set_alpha(self._alpha)
        bg_rect = bg.get_rect(center=(self.x, self.y))
        screen.blit(bg, bg_rect)

        # Draw text
        text = self._text_surf.copy()
        text.set_alpha(self._alpha)
        text_rect = text.get_rect(center=(self.x, self.y))
        screen.blit(text, text_rect)

    def is_done(self) -> bool:
        return self._done


class TutorialManager:
    """Manages a sequence of tutorial hints."""

    def __init__(self) -> None:
        self.hints: list[TutorialHint] = []
        self.current_index = 0
        self._started = False

    def add_hint(self, hint: TutorialHint) -> None:
        self.hints.append(hint)

    def start(self) -> None:
        self._started = True
        self.current_index = 0

    def update(self, dt: float) -> None:
        if not self._started or self.current_index >= len(self.hints):
            return

        current = self.hints[self.current_index]
        current.update(dt)

        if current.is_done():
            self.current_index += 1

    def draw(self, screen: pygame.Surface) -> None:
        if not self._started or self.current_index >= len(self.hints):
            return

        self.hints[self.current_index].draw(screen)

    def is_complete(self) -> bool:
        return self._started and self.current_index >= len(self.hints)
