"""Tests for app context wiring and scene bootstrap behavior."""

import pygame

from shadow_mario.app_context import AppContext, hydrate_audio_settings
from shadow_mario.scene_payloads import LevelStartPayload
from shadow_mario.scenes.scene import Scene
from shadow_mario.scenes.scene_manager import SceneManager


class _DummySave:
    def __init__(self):
        self._settings = {
            "master_volume": 0.5,
            "bgm_volume": 0.4,
            "sfx_volume": 0.3,
            "muted": True,
        }

    def get_audio_settings(self):
        return dict(self._settings)


class _DummyAudio:
    def __init__(self):
        self.loaded = None

    def load_settings(self, settings):
        self.loaded = dict(settings)


class _DummyScene(Scene):
    def __init__(self, context):
        super().__init__(context)
        self.enter_payload = {}

    def on_enter(self, data=None):
        super().on_enter(data)
        self.enter_payload = dict(self._transition_data)

    def handle_events(self, events):
        return None

    def update(self, dt):
        return None

    def draw(self, screen):
        return None


def test_hydrate_audio_settings_uses_saved_values():
    save = _DummySave()
    audio = _DummyAudio()
    hydrate_audio_settings(save, audio)
    assert audio.loaded == save.get_audio_settings()


def test_scene_manager_injects_shared_context():
    context = AppContext(config=object(), save=object(), audio=object(), runtime_config=object())
    screen = pygame.Surface((16, 16))
    manager = SceneManager(screen, context)
    manager.register("dummy", _DummyScene)
    manager.replace("dummy", LevelStartPayload(level=4))
    manager.apply_pending()

    scene = manager.current_scene()
    assert scene is not None
    assert scene.context is context
    assert scene.enter_payload["level"] == 4
