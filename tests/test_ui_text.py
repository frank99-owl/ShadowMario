"""Every string the UI draws must be drawable by the game's font.

FSO8BITR.TTF has no glyph for : ? % / ( ) + | and several other characters;
they render as boxes. Until October 2026 the menu showed "COINS▯ 346", every
loading screen "45▯", and the pause screen's help line was half boxes. This
renders each scene for a while, records every string drawn, and fails on any
that contains a character the font lacks.
"""

import dataclasses
import traceback
from pathlib import Path

import pygame
import pytest

from shadow_mario.scene_payloads import GameOverPayload

FONT_PATH = Path(__file__).resolve().parent.parent / "res" / "FSO8BITR.TTF"


def _missing_glyphs() -> set[str]:
    font = pygame.font.Font(str(FONT_PATH), 24)
    tofu = pygame.image.tostring(font.render("￿", False, (255, 255, 255)), "RGB")
    return {
        ch for ch in map(chr, range(32, 127))
        if pygame.image.tostring(font.render(ch, False, (255, 255, 255)), "RGB") == tofu
    }


@pytest.fixture
def drawn_text(monkeypatch):
    """Map of every string the game's own code renders while active -> file:line."""
    drawn: dict[str, str] = {}
    base = pygame.font.Font

    class RecordingFont(base):
        def render(self, text, *args, **kwargs):
            caller = [f for f in traceback.extract_stack()[:-1] if "shadow_mario" in f.filename]
            if caller and isinstance(text, str) and text.strip():
                drawn.setdefault(text, f"{Path(caller[-1].filename).name}:{caller[-1].lineno}")
            return super().render(text, *args, **kwargs)

    monkeypatch.setattr(pygame.font, "Font", RecordingFont)
    return drawn


def _play(scene, screen, data=None, frames=60):
    if data is not None and dataclasses.is_dataclass(data):
        data = dataclasses.asdict(data)
    scene.on_enter(data)
    for _ in range(frames):
        scene.update(1 / 60)
        scene.draw(screen)


def test_font_really_lacks_the_glyphs_this_test_guards():
    missing = _missing_glyphs()
    assert {":", "%", "|", "?", "/"} <= missing
    assert not {"-", "!", ".", ","} & missing  # what the UI uses instead


@pytest.fixture
def missing():
    # Computed before drawn_text starts recording, with the real Font class.
    return _missing_glyphs()


def test_every_scene_draws_only_characters_the_font_has(missing, drawn_text):
    from shadow_mario.app_context import build_app_context
    from shadow_mario.scenes import (
        GameOverScene, GameScene, LevelSelectScene, LoadingScene, MenuScene, PauseScene, SettingsScene,
    )

    screen = pygame.display.set_mode((1024, 768))
    context = build_app_context()
    context.save.add_coins(5)  # the menu only shows its totals once there are some
    context.save.set_high_score(1, 9)

    _play(MenuScene(context), screen)
    _play(LevelSelectScene(context), screen)
    _play(SettingsScene(context), screen)
    _play(LoadingScene(context), screen, {"level": 1}, frames=120)
    for level in (1, 2, 3, 4):
        _play(GameScene(context), screen, {"level": level}, frames=90)
    paused = GameScene(context)
    paused.on_enter({"level": 1})
    paused._paused = True
    _play(paused, screen, None, frames=5)
    _play(PauseScene(context), screen, {"level": 1})
    for result in (
        GameOverPayload(won=True, level=1, score=24, health=0.64, elapsed_time=13.2,
                        total_coins=33, collected_coins=24),
        GameOverPayload(won=False, level=3, score=5, health=0.0, elapsed_time=40.0,
                        total_coins=40, collected_coins=5),
        GameOverPayload(won=True, level=4, score=0, health=50.0, elapsed_time=70.0,
                        total_coins=80, collected_coins=30, p1_score=17, p2_score=12, race_winner=1),
    ):
        _play(GameOverScene(context), screen, result)

    # The loading screen shows one random tip, typed out; check them all.
    for tip in LoadingScene.TIPS:
        drawn_text.setdefault(tip, "loading_scene.py (TIPS)")

    bad = {
        "".join("▯" if c in missing else c for c in text): where
        for text, where in drawn_text.items()
        if any(c in missing for c in text)
    }
    assert len(drawn_text) > 50, "the scenes drew almost nothing; the recording is broken"
    assert not bad, "text the font cannot draw (▯ marks the box):\n" + "\n".join(
        f"  {where}: {text}" for text, where in sorted(bad.items(), key=lambda kv: kv[1])
    )
