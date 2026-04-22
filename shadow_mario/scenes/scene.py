"""Scene abstract base class."""

from abc import ABC, abstractmethod
from typing import List

import pygame


class Scene(ABC):
    """Abstract base class for all game scenes.

    Each scene is responsible for handling its own events, update logic, and rendering.
    Scenes are switched via SceneManager.
    """

    def __init__(self) -> None:
        self._is_done = False
        self._next_scene_name: str | None = None
        self._transition_data: dict = {}

    @abstractmethod
    def handle_events(self, events: List[pygame.event.Event]) -> None:
        """Handle input events."""
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update scene logic, dt is seconds from last frame to current frame."""
        ...

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """Draw scene content to screen."""
        ...

    def is_done(self) -> bool:
        """Return whether scene is done and needs switching."""
        return self._is_done

    def get_next_scene_name(self) -> str | None:
        """Return the name of the next scene."""
        return self._next_scene_name

    def get_transition_data(self) -> dict:
        """Return data passed to the next scene."""
        return self._transition_data

    def _switch_to(self, scene_name: str, data: dict | None = None) -> None:
        """Request switching to the specified scene."""
        self._is_done = True
        self._next_scene_name = scene_name
        self._transition_data = data or {}

    def on_enter(self, data: dict | None = None) -> None:
        """Called when scene enters, subclasses may override."""
        self._is_done = False
        self._next_scene_name = None
        self._transition_data = data or {}

    def on_exit(self) -> None:
        """Called when scene exits, subclasses may override."""
        pass
