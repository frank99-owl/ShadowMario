"""Scene abstract base class."""

from abc import ABC, abstractmethod
from typing import Any, List, Mapping

import pygame

from shadow_mario.app_context import AppContext


class Scene(ABC):
    """Abstract base class for all game scenes.

    Each scene is responsible for handling its own events, update logic, and rendering.
    Scenes are switched via SceneManager.
    """

    def __init__(self, context: AppContext) -> None:
        self.context = context
        self._is_done = False
        self._next_scene_name: str | None = None
        self._transition_data: dict[str, Any] = {}

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

    def get_transition_data(self) -> dict[str, Any]:
        """Return data passed to the next scene."""
        return self._transition_data

    def _normalize_transition_data(self, data: Any | None) -> dict[str, Any]:
        if data is None:
            return {}
        if isinstance(data, Mapping):
            return dict(data)
        to_dict = getattr(data, "to_dict", None)
        if callable(to_dict):
            converted = to_dict()
            if isinstance(converted, Mapping):
                return dict(converted)
        return {}

    def _switch_to(self, scene_name: str, data: Any | None = None) -> None:
        """Request switching to the specified scene."""
        self._is_done = True
        self._next_scene_name = scene_name
        self._transition_data = self._normalize_transition_data(data)

    def on_enter(self, data: Mapping[str, Any] | None = None) -> None:
        """Called when scene enters, subclasses may override."""
        self._is_done = False
        self._next_scene_name = None
        self._transition_data = self._normalize_transition_data(data)

    def on_exit(self) -> None:
        """Called when scene exits, subclasses may override."""
        pass
