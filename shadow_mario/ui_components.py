"""UI components for the game."""

import pygame


class Slider:
    """A horizontal slider UI component."""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        min_value: float = 0.0,
        max_value: float = 1.0,
        initial_value: float = 0.5,
        label: str = "",
    ) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.label = label
        self._dragging = False

        # Colors
        self.track_color = (60, 60, 80)
        self.fill_color = (100, 150, 255)
        self.handle_color = (200, 200, 255)
        self.handle_hover_color = (255, 255, 255)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events. Returns True if value changed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._dragging = True
                self._update_value_from_pos(event.pos[0])
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False

        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._update_value_from_pos(event.pos[0])
            return True

        return False

    def _update_value_from_pos(self, mouse_x: float) -> None:
        ratio = (mouse_x - self.x) / self.width
        self.value = max(self.min_value, min(self.max_value, ratio))

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        # Track background
        track_rect = pygame.Rect(self.x, self.y + self.height // 2 - 3, self.width, 6)
        pygame.draw.rect(screen, self.track_color, track_rect, border_radius=3)

        # Filled portion
        fill_width = int(self.width * self.value)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.x, self.y + self.height // 2 - 3, fill_width, 6)
            pygame.draw.rect(screen, self.fill_color, fill_rect, border_radius=3)

        # Handle
        handle_x = self.x + fill_width
        handle_y = self.y + self.height // 2
        handle_radius = 8

        mouse_pos = pygame.mouse.get_pos()
        dist = ((mouse_pos[0] - handle_x) ** 2 + (mouse_pos[1] - handle_y) ** 2) ** 0.5
        color = self.handle_hover_color if dist < handle_radius + 5 else self.handle_color

        pygame.draw.circle(screen, color, (int(handle_x), int(handle_y)), handle_radius)
        pygame.draw.circle(screen, (80, 80, 120), (int(handle_x), int(handle_y)), handle_radius, width=2)

        # Label
        if self.label:
            label_surf = font.render(self.label, True, (255, 255, 255))
            screen.blit(label_surf, (self.x, self.y - 25))

        # Value text
        pct = int(self.value * 100)
        value_surf = font.render(f"{pct}", True, (200, 200, 200))
        screen.blit(value_surf, (self.x + self.width + 10, self.y + self.height // 2 - value_surf.get_height() // 2))
