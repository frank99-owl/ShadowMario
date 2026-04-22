"""Save system, manages player progress and settings."""

import json
import os
from typing import Optional, Dict, Any


class SaveManager:
    """Manages game save data.

    Save contents:
    - High scores (per level + global)
    - Level completion status (unlocked/locked)
    - Total coins
    - Audio settings
    - Key bindings
    """

    _instance: Optional["SaveManager"] = None

    def __new__(cls) -> "SaveManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.save_path = os.path.join(base_dir, "save.json")

        # Default data
        self.data: Dict[str, Any] = {
            "version": 1,
            "high_scores": {  # Per level high scores
                "1": 0,
                "2": 0,
                "3": 0,
                "4": 0,
            },
            "best_times": {  # Per level best time (seconds), 0 = no record
                "1": 0,
                "2": 0,
                "3": 0,
                "4": 0,
            },
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
            "achievements": {},  # Achievement system reserved
        }

        self._load()

    def _load(self) -> None:
        """Load save from file."""
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Merge loaded data (keep defaults as fallback)
                    self._merge_data(loaded)
            except (json.JSONDecodeError, IOError):
                pass

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
        """Save current data to file."""
        try:
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

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
        self.data = {
            "version": 1,
            "high_scores": {"1": 0, "2": 0, "3": 0, "4": 0},
            "best_times": {"1": 0, "2": 0, "3": 0, "4": 0},
            "unlocked_levels": [True, True, True, True],
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
        self.save()


def get_save_manager() -> SaveManager:
    """Get SaveManager singleton."""
    return SaveManager()
