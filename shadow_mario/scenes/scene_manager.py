"""Scene manager, responsible for scene switching and lifecycle management."""

from typing import Any, Dict, Mapping, Type

import pygame

from shadow_mario.app_context import AppContext

from .scene import Scene


class SceneManager:
    """Stack-based scene switcher for managing game scenes.

    Supports:
    - Scene switching (replace)
    - Scene push (push, for overlays like pause)
    - Scene pop (pop, return to previous scene)
    """

    def __init__(self, screen: pygame.Surface, context: AppContext) -> None:
        self._screen = screen
        self._context = context
        self._scenes: Dict[str, Type[Scene]] = {}
        self._stack: list[Scene] = []
        self._pending_push: str | None = None
        self._pending_pop = False
        self._pending_replace: tuple[str, dict[str, Any]] | None = None
        self._pending_data: dict[str, Any] = {}

    def register(self, name: str, scene_cls: Type[Scene]) -> None:
        """Register a scene class."""
        self._scenes[name] = scene_cls

    def _normalize_data(self, data: Any | None) -> dict[str, Any]:
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

    def push(self, name: str, data: Any | None = None) -> None:
        """Push a new scene onto the stack (overlay current scene)."""
        self._pending_push = name
        self._pending_data = self._normalize_data(data)

    def pop(self) -> None:
        """Pop current scene, return to previous scene."""
        self._pending_pop = True

    def replace(self, name: str, data: Any | None = None) -> None:
        """Replace current scene with a new scene."""
        self._pending_replace = (name, self._normalize_data(data))

    def _create_scene(self, name: str) -> Scene:
        """Create a scene instance."""
        if name not in self._scenes:
            raise KeyError(f"Unregistered scene: {name}")
        return self._scenes[name](self._context)

    def apply_pending(self) -> None:
        """Apply pending scene switching operations."""
        if self._pending_pop:
            if self._stack:
                self._stack[-1].on_exit()
                self._stack.pop()
            if self._stack:
                self._stack[-1].on_enter({})
            self._pending_pop = False

        elif self._pending_push:
            if self._stack:
                # When overlay scene enters, don't exit the underlying scene
                pass
            scene = self._create_scene(self._pending_push)
            scene.on_enter(self._pending_data)
            self._stack.append(scene)
            self._pending_push = None
            self._pending_data = {}

        elif self._pending_replace:
            name, data = self._pending_replace
            if self._stack:
                self._stack[-1].on_exit()
                self._stack.pop()
            scene = self._create_scene(name)
            scene.on_enter(data)
            self._stack.append(scene)
            self._pending_replace = None

    def _apply_pending(self) -> None:
        """Backward-compatible alias for legacy calls."""
        self.apply_pending()

    def update(self, dt: float) -> None:
        """Update current scene (does not auto-handle scene switching, controlled by main loop)."""
        if not self._stack:
            return
        self._stack[-1].update(dt)

    def draw(self) -> None:
        """Draw scene stack (from bottom to top)."""
        # Clear screen to prevent remnants from previous scenes or frames
        self._screen.fill((0, 0, 0))
        
        for scene in self._stack:
            scene.draw(self._screen)

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        """Pass events to the top scene on the stack."""
        if not self._stack:
            return
        # Only pass events to top scene (overlay scenes handle first)
        self._stack[-1].handle_events(events)

    def is_empty(self) -> bool:
        """Whether the scene stack is empty."""
        return len(self._stack) == 0

    def current_scene(self) -> Scene | None:
        """Return current active scene."""
        if not self._stack:
            return None
        return self._stack[-1]
