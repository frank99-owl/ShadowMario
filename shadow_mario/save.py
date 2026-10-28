"""Save system, manages player progress and settings.

Where the save lives is `storage.default_store()`'s decision: a file in the
user's data folder on desktop, window.localStorage in the browser.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from .storage import LEGACY_SAVE_PATH, Store, default_store, is_browser

SAVE_NAME = "save.json"

_DEFAULT_DATA: dict[str, Any] = {
    "version": 1,
    "high_scores": {"1": 0, "2": 0, "3": 0, "4": 0},  # Per level high scores
    "best_times": {"1": 0, "2": 0, "3": 0, "4": 0},  # Seconds per level, 0 = no record
    "unlocked_levels": [True, True, True, True],  # Level unlock status
    "total_coins": 0,
    "audio_settings": {
        "master_volume": 1.0,
        "bgm_volume": 0.7,
        "sfx_volume": 0.8,
        "muted": False,
    },
    "key_bindings": {
        "left": "K_LEFT",
        "right": "K_RIGHT",
        "jump": "K_UP",
        "shoot": "K_s",
        "pause": "K_ESCAPE",
    },
    "achievements": {},
}


def default_data() -> dict[str, Any]:
    return copy.deepcopy(_DEFAULT_DATA)


class SaveManager:
    """Manages game save data.

    Save contents:
    - High scores (per level + global)
    - Level completion status (unlocked/locked)
    - Total coins
    - Audio settings
    - Key bindings
    """

    def __init__(self, store: Store, legacy_path: Path | None = None) -> None:
        self.store = store
        self.data: dict[str, Any] = default_data()
        self._load(legacy_path)

    def _load(self, legacy_path: Path | None) -> None:
        """Load the save; adopt a pre-October-2026 save.json from beside the code once."""
        text = self.store.read(SAVE_NAME)
        migrating = False
        if text is None and legacy_path is not None:
            try:
                text = legacy_path.read_text(encoding="utf-8")
                migrating = True
            except (OSError, UnicodeDecodeError):
                text = None
        if text is None:
            return
        try:
            loaded = json.loads(text)
            if not isinstance(loaded, dict):
                raise ValueError("save is not a JSON object")
            self._merge_data(loaded)
        except (ValueError, TypeError, AttributeError):
            # Start from defaults, but move the unreadable save aside first: the
            # next save() would otherwise overwrite the only copy of it.
            self.data = default_data()
            if not migrating:
                self.store.quarantine(SAVE_NAME)
            return
        if migrating:
            self.save()

    def _merge_data(self, loaded: dict) -> None:
        """Merge loaded data into current data structure."""
        for key, value in loaded.items():
            if key in self.data and isinstance(value, dict) and isinstance(self.data[key], dict):
                self.data[key].update(value)
            else:
                self.data[key] = value
        # Upgrade old saves to include level 4 keys and unlock status.
        for level_key in ("1", "2", "3", "4"):
            self.data["high_scores"].setdefault(level_key, 0)
            self.data["best_times"].setdefault(level_key, 0)
        while len(self.data["unlocked_levels"]) < 4:
            self.data["unlocked_levels"].append(True)

    def save(self) -> None:
        """Write the save. A failure is reported and the previous save stays intact."""
        # ASCII-only JSON: pygbag's bridge stores a string's UTF-8 bytes as
        # Latin-1 characters in localStorage, so non-ASCII text would not come
        # back as written. \u escapes survive.
        text = json.dumps(self.data, indent=2, ensure_ascii=True)
        try:
            self.store.write(SAVE_NAME, text)
        except OSError as exc:
            print(f"[save] could not write {SAVE_NAME}: {exc}", file=sys.stderr)

    # ---- High scores ----

    def get_high_score(self, level: int) -> int:
        """Get high score for the specified level."""
        return self.data["high_scores"].get(str(level), 0)

    def set_high_score(self, level: int, score: int) -> bool:
        """Set high score (only when new score is higher), returns whether updated."""
        key = str(level)
        current = self.data["high_scores"].get(key, 0)
        if score > current:
            self.data["high_scores"][key] = score
            self.save()
            return True
        return False

    # ---- Best times ----

    def get_best_time(self, level: int) -> float:
        """Get best time (seconds) for the specified level, 0 if no record."""
        return self.data["best_times"].get(str(level), 0)

    def set_best_time(self, level: int, elapsed: float) -> bool:
        """Set best time (only when new time is lower and > 0), returns whether updated."""
        key = str(level)
        current = self.data["best_times"].get(key, 0)
        if elapsed > 0 and (current == 0 or elapsed < current):
            self.data["best_times"][key] = elapsed
            self.save()
            return True
        return False

    # ---- Level unlocks ----

    def is_level_unlocked(self, level: int) -> bool:
        """Check if level is unlocked."""
        levels = self.data["unlocked_levels"]
        if 0 <= level - 1 < len(levels):
            return levels[level - 1]
        return False

    def unlock_level(self, level: int) -> None:
        """Unlock the specified level."""
        levels = self.data["unlocked_levels"]
        while len(levels) < level:
            levels.append(False)
        if level > 0:
            levels[level - 1] = True
        self.save()

    def get_unlocked_levels(self) -> list[bool]:
        """Get all level unlock statuses."""
        return list(self.data["unlocked_levels"])

    # ---- Coins ----

    def add_coins(self, amount: int) -> None:
        """Add to total coin count."""
        self.data["total_coins"] += amount
        self.save()

    def get_total_coins(self) -> int:
        """Get total coin count."""
        return self.data["total_coins"]

    # ---- Audio settings ----

    def get_audio_settings(self) -> dict:
        """Get audio settings."""
        return dict(self.data["audio_settings"])

    def set_audio_settings(self, settings: dict) -> None:
        """Set audio settings."""
        self.data["audio_settings"].update(settings)
        self.save()

    # ---- Key bindings ----

    def get_key_bindings(self) -> dict:
        """Get key bindings."""
        return dict(self.data["key_bindings"])

    def set_key_binding(self, action: str, key: str) -> None:
        """Set key binding."""
        self.data["key_bindings"][action] = key
        self.save()

    # ---- Achievements (reserved) ----

    def unlock_achievement(self, achievement_id: str) -> bool:
        """Unlock achievement, returns whether it was the first time."""
        if achievement_id not in self.data["achievements"]:
            self.data["achievements"][achievement_id] = True
            self.save()
            return True
        return False

    def has_achievement(self, achievement_id: str) -> bool:
        """Check if achievement is unlocked."""
        return self.data["achievements"].get(achievement_id, False)

    def reset(self) -> None:
        """Reset all save data."""
        self.data = default_data()
        self.save()


_instance: SaveManager | None = None


def get_save_manager() -> SaveManager:
    """The process-wide SaveManager, created on first use."""
    global _instance
    if _instance is None:
        legacy = None if is_browser() else LEGACY_SAVE_PATH
        _instance = SaveManager(default_store(), legacy_path=legacy)
    return _instance
