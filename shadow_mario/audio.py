"""Sound effects and music management system."""

import os
from typing import Dict, Optional

import pygame


class AudioManager:
    """Manages game sound effects and background music.

    Supports:
    - Background music (BGM) play/pause/switch
    - Sound effects (SFX) playback
    - Independent volume control (master, BGM, SFX)
    - Mute toggle
    """

    _instance: Optional["AudioManager"] = None

    def __new__(cls) -> "AudioManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        # Volume settings (0.0 - 1.0)
        self.master_volume = 1.0
        self.bgm_volume = 0.7
        self.sfx_volume = 0.8
        self._muted = True

        # Audio resource path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sounds_dir = os.path.join(base_dir, "res", "sounds")

        # Loaded sound effects cache
        self._sfx_cache: Dict[str, pygame.mixer.Sound] = {}
        self._current_bgm: Optional[str] = None

        # Initialize mixer
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._mixer_available = True
        except pygame.error:
            self._mixer_available = False

    def _get_path(self, filename: str) -> str:
        """Get the full path to an audio file."""
        return os.path.join(self.sounds_dir, filename)

    def _load_sfx(self, name: str) -> Optional[pygame.mixer.Sound]:
        """Load a sound effect into cache."""
        if name in self._sfx_cache:
            return self._sfx_cache[name]

        path = self._get_path(f"{name}.wav")
        if not os.path.exists(path):
            path = self._get_path(f"{name}.ogg")
        if not os.path.exists(path):
            return None

        try:
            sound = pygame.mixer.Sound(path)
            self._sfx_cache[name] = sound
            return sound
        except pygame.error:
            return None

    def play_sfx(self, name: str) -> None:
        """Play a sound effect."""
        if not self._mixer_available or self._muted:
            return

        sound = self._load_sfx(name)
        if sound:
            volume = self.master_volume * self.sfx_volume
            sound.set_volume(volume)
            sound.play()

    def play_bgm(self, name: str, loops: int = -1, fade_ms: int = 500) -> None:
        """Play background music."""
        if not self._mixer_available:
            return

        if self._current_bgm == name and pygame.mixer.music.get_busy():
            return

        for ext in [".ogg", ".mp3", ".wav"]:
            path = self._get_path(f"{name}{ext}")
            if os.path.exists(path):
                break
        else:
            return

        try:
            pygame.mixer.music.load(path)
            volume = 0.0 if self._muted else self.master_volume * self.bgm_volume
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops, fade_ms=fade_ms)
            self._current_bgm = name
        except pygame.error:
            pass

    def stop_bgm(self, fade_ms: int = 500) -> None:
        """Stop background music."""
        if self._mixer_available:
            pygame.mixer.music.fadeout(fade_ms)
            self._current_bgm = None

    def pause_bgm(self) -> None:
        """Pause background music."""
        if self._mixer_available and pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()

    def resume_bgm(self) -> None:
        """Resume background music."""
        if self._mixer_available:
            pygame.mixer.music.unpause()

    def set_master_volume(self, volume: float) -> None:
        """Set master volume."""
        self.master_volume = max(0.0, min(1.0, volume))
        self._apply_volumes()

    def set_bgm_volume(self, volume: float) -> None:
        """Set background music volume."""
        self.bgm_volume = max(0.0, min(1.0, volume))
        self._apply_volumes()

    def set_sfx_volume(self, volume: float) -> None:
        """Set sound effects volume."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        self._apply_volumes()

    def _apply_volumes(self) -> None:
        """Apply current volume settings."""
        if not self._mixer_available:
            return

        bgm_vol = 0.0 if self._muted else self.master_volume * self.bgm_volume
        pygame.mixer.music.set_volume(bgm_vol)

        sfx_vol = 0.0 if self._muted else self.master_volume * self.sfx_volume
        for sound in self._sfx_cache.values():
            sound.set_volume(sfx_vol)

    def toggle_mute(self) -> bool:
        """Toggle mute state, returns whether currently muted."""
        self._muted = not self._muted
        self._apply_volumes()
        return self._muted

    def is_muted(self) -> bool:
        """Return whether muted."""
        return self._muted

    def get_settings(self) -> dict:
        """Get current audio settings (for saving)."""
        return {
            "master_volume": self.master_volume,
            "bgm_volume": self.bgm_volume,
            "sfx_volume": self.sfx_volume,
            "muted": self._muted,
        }

    def load_settings(self, settings: dict) -> None:
        """Load audio settings from save."""
        self.master_volume = settings.get("master_volume", 1.0)
        self.bgm_volume = settings.get("bgm_volume", 0.7)
        self.sfx_volume = settings.get("sfx_volume", 0.8)
        self._muted = settings.get("muted", False)
        self._apply_volumes()


def get_audio_manager() -> AudioManager:
    """Get AudioManager singleton."""
    return AudioManager()
