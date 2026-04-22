"""Typed payload models for scene transitions."""

from dataclasses import asdict, dataclass
from typing import Any, Mapping


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class LevelStartPayload:
    """Transition payload for starting a level."""

    level: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "LevelStartPayload":
        if data is None:
            return cls()
        return cls(level=max(1, _to_int(data.get("level", 1), 1)))


@dataclass(frozen=True)
class SettingsRoutePayload:
    """Transition payload for settings scene navigation."""

    return_to: str = "menu"
    level: int = 1
    pause_data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "SettingsRoutePayload":
        if data is None:
            return cls()
        return cls(
            return_to=str(data.get("return_to", "menu")),
            level=max(1, _to_int(data.get("level", 1), 1)),
            pause_data=dict(data.get("pause_data", {})) if isinstance(data.get("pause_data"), Mapping) else None,
        )


@dataclass(frozen=True)
class GameOverPayload:
    """Transition payload for game over scene."""

    won: bool
    level: int
    score: int = 0
    health: float = 0.0
    elapsed_time: float = 0.0
    total_coins: int = 0
    collected_coins: int = 0
    p1_score: int = 0
    p2_score: int = 0
    race_winner: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "GameOverPayload":
        if data is None:
            return cls(won=False, level=1)
        winner = data.get("race_winner")
        winner_int = None
        if winner is not None:
            winner_int = _to_int(winner, 0)
        return cls(
            won=bool(data.get("won", False)),
            level=max(1, _to_int(data.get("level", 1), 1)),
            score=_to_int(data.get("score", 0), 0),
            health=_to_float(data.get("health", 0.0), 0.0),
            elapsed_time=max(0.0, _to_float(data.get("elapsed_time", 0.0), 0.0)),
            total_coins=max(0, _to_int(data.get("total_coins", 0), 0)),
            collected_coins=max(0, _to_int(data.get("collected_coins", 0), 0)),
            p1_score=_to_int(data.get("p1_score", 0), 0),
            p2_score=_to_int(data.get("p2_score", 0), 0),
            race_winner=winner_int,
        )
