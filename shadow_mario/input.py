"""Compact, recordable keyboard state for the gameplay simulation."""

from __future__ import annotations

import pygame

# Every key the level simulation reads. The bit order is part of the replay
# file format: append new keys at the end, never reorder.
TRACKED_KEYS: tuple[int, ...] = (
    pygame.K_LEFT,
    pygame.K_RIGHT,
    pygame.K_UP,
    pygame.K_s,
    pygame.K_a,
    pygame.K_d,
    pygame.K_w,
)
_BIT = {key: 1 << i for i, key in enumerate(TRACKED_KEYS)}


class InputFrame:
    """Key lookup with the same `frame[pygame.K_x]` interface as pygame.key.get_pressed()."""

    __slots__ = ("mask",)

    def __init__(self, mask: int = 0) -> None:
        self.mask = mask

    @classmethod
    def from_pressed(cls, pressed) -> "InputFrame":
        mask = 0
        for key, bit in _BIT.items():
            if pressed[key]:
                mask |= bit
        return cls(mask)

    @classmethod
    def of(cls, *keys: int) -> "InputFrame":
        mask = 0
        for key in keys:
            mask |= _BIT[key]
        return cls(mask)

    def __getitem__(self, key: int) -> bool:
        bit = _BIT.get(key)
        return bool(bit and self.mask & bit)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, InputFrame) and other.mask == self.mask

    def __hash__(self) -> int:
        return self.mask

    def __repr__(self) -> str:
        return f"InputFrame({self.mask:#x})"
