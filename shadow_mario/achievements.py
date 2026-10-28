"""Achievement system."""

from __future__ import annotations

from typing import Callable, Optional

from shadow_mario.save import SaveManager, get_save_manager


class Achievement:
    """Single achievement definition."""

    def __init__(self, id: str, name: str, description: str, icon: str = "") -> None:
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon


SPEED_RUN_SECONDS = 60.0


class AchievementManager:
    """Manages game achievements."""

    def __init__(self, save: SaveManager) -> None:
        self.save = save

        # Achievement definitions
        self.achievements: dict[str, Achievement] = {
            "first_blood": Achievement("first_blood", "First Blood", "Complete Level 1"),
            "sky_walker": Achievement("sky_walker", "Sky Walker", "Complete Level 2"),
            "boss_slayer": Achievement("boss_slayer", "Boss Slayer", "Defeat the Boss in Level 3"),
            "coin_collector": Achievement("coin_collector", "Coin Collector", "Collect 50 coins in total"),
            "no_damage": Achievement("no_damage", "Untouchable", "Complete a level without taking damage"),
            "speed_run": Achievement("speed_run", "Speed Runner", "Complete Level 1 in under 60 seconds"),
        }

        # Achievement unlock callback
        self.on_unlock: Optional[Callable[[Achievement], None]] = None

    def unlock(self, achievement_id: str) -> bool:
        """Unlock an achievement, returns whether it was the first time."""
        if achievement_id not in self.achievements:
            return False

        first_time = self.save.unlock_achievement(achievement_id)
        if first_time and self.on_unlock:
            self.on_unlock(self.achievements[achievement_id])
        return first_time

    def is_unlocked(self, achievement_id: str) -> bool:
        """Check if an achievement is unlocked."""
        return self.save.has_achievement(achievement_id)

    def get_all(self) -> list[Achievement]:
        """Get all achievement definitions."""
        return list(self.achievements.values())

    def get_unlocked(self) -> list[Achievement]:
        """Get all unlocked achievements."""
        return [a for a in self.achievements.values() if self.is_unlocked(a.id)]

    def check_level_complete(self, level: int, score: int, health: float, *,
                             max_health: float, elapsed_time: float) -> list[str]:
        """Check level completion related achievements, returns list of newly unlocked achievement IDs.

        Call it after the level's coins are in the save: the coin total is read
        from the save alone. Adding the level's coins again here counted them
        twice, so "Collect 50 coins in total" unlocked after 25.

        `max_health` is the level's starting health: 1.0 in levels 1-3, 100 in
        the race. Comparing against 1.0 everywhere made any race win count as
        "without taking damage".
        """
        unlocked = []

        if level == 1:
            if self.unlock("first_blood"):
                unlocked.append("first_blood")
        elif level == 2:
            if self.unlock("sky_walker"):
                unlocked.append("sky_walker")
        elif level == 3:
            if self.unlock("boss_slayer"):
                unlocked.append("boss_slayer")

        # Was defined but never checked, so it could not be earned.
        if level == 1 and 0 < elapsed_time < SPEED_RUN_SECONDS:
            if self.unlock("speed_run"):
                unlocked.append("speed_run")

        # No damage clear: still at this level's full health
        if health >= max_health:
            if self.unlock("no_damage"):
                unlocked.append("no_damage")

        # Coin collection
        if self.save.get_total_coins() >= 50:
            if self.unlock("coin_collector"):
                unlocked.append("coin_collector")

        return unlocked


_instance: AchievementManager | None = None


def get_achievement_manager() -> AchievementManager:
    """The process-wide AchievementManager, bound to the process-wide save."""
    global _instance
    if _instance is None:
        _instance = AchievementManager(get_save_manager())
    return _instance
