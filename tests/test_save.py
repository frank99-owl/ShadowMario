"""Save persistence: where it lives, how it is written, and what survives."""

import json
import os
import platform
import sys
from pathlib import Path

import pytest

from shadow_mario import storage
from shadow_mario.save import SAVE_NAME, SaveManager, default_data
from shadow_mario.storage import BrowserStore, FileStore, default_store, user_data_dir


class FakeLocalStorage:
    """window.localStorage as pygbag's bridge presents it.

    Measured in Chromium (pygbag 0.9.3): getItem of a missing key returns None,
    and setItem stores a str's UTF-8 bytes as Latin-1 characters, so "é" reads
    back as "Ã©".
    """

    def __init__(self) -> None:
        self.items: dict[str, str] = {}

    def getItem(self, key):  # noqa: N802 - JavaScript name
        return self.items.get(key)

    def setItem(self, key, value):  # noqa: N802
        self.items[key] = value.encode("utf-8").decode("latin-1")

    def removeItem(self, key):  # noqa: N802
        self.items.pop(key, None)


class BlockedLocalStorage:
    """Storage refused by the browser: every call throws."""

    def getItem(self, key):  # noqa: N802
        raise RuntimeError("SecurityError: access is denied")

    setItem = removeItem = getItem


# ---- where the save lives ----

def test_user_data_dir_follows_each_os_convention(tmp_path):
    home = tmp_path / "home"
    assert user_data_dir({}, "darwin", home) == home / "Library" / "Application Support" / "ShadowMario"
    assert user_data_dir({"APPDATA": str(tmp_path / "Roaming")}, "win32", home) == tmp_path / "Roaming" / "ShadowMario"
    assert user_data_dir({}, "win32", home) == home / "AppData" / "Roaming" / "ShadowMario"
    assert user_data_dir({}, "linux", home) == home / ".local" / "share" / "shadow-mario"
    assert user_data_dir({"XDG_DATA_HOME": str(tmp_path / "xdg")}, "linux", home) == tmp_path / "xdg" / "shadow-mario"
    assert user_data_dir({"SHADOW_MARIO_DATA_DIR": str(tmp_path / "x")}, "darwin", home) == tmp_path / "x"


def test_desktop_default_is_a_file_in_the_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("SHADOW_MARIO_DATA_DIR", str(tmp_path))
    store = default_store()
    assert isinstance(store, FileStore) and store.directory == tmp_path


def test_browser_default_is_local_storage(monkeypatch):
    local = FakeLocalStorage()
    monkeypatch.setattr(sys, "platform", "emscripten")
    monkeypatch.setattr(platform, "window", type("Window", (), {"localStorage": local})(), raising=False)
    store = default_store()
    assert isinstance(store, BrowserStore)
    store.write("save.json", "{}")
    assert local.items == {"shadowmario/save.json": "{}"}


def test_tests_never_touch_the_real_save():
    # conftest points the data dir at a temp folder for the whole session.
    assert Path(os.environ["SHADOW_MARIO_DATA_DIR"]) != user_data_dir({}, sys.platform)


# ---- atomic file writes ----

def test_file_store_round_trip_and_missing_file(tmp_path):
    store = FileStore(tmp_path / "nested")
    assert store.read("save.json") is None
    store.write("save.json", "hello")
    assert store.read("save.json") == "hello"


@pytest.mark.parametrize("failing", ["fsync", "replace"])
def test_failed_write_keeps_the_previous_save(tmp_path, monkeypatch, failing):
    store = FileStore(tmp_path)
    store.write("save.json", "previous")

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(storage.os, failing, boom)
    with pytest.raises(OSError):
        store.write("save.json", "x" * 10_000)
    assert (tmp_path / "save.json").read_text() == "previous"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["save.json"]  # no temp file left


def test_save_manager_reports_a_failed_write_without_crashing(tmp_path, monkeypatch, capsys):
    store = FileStore(tmp_path)
    manager = SaveManager(store)
    manager.add_coins(5)
    monkeypatch.setattr(storage.os, "replace", lambda *a: (_ for _ in ()).throw(OSError("read-only")))
    manager.add_coins(5)  # must not raise
    assert "could not write save.json" in capsys.readouterr().err
    assert json.loads((tmp_path / SAVE_NAME).read_text())["total_coins"] == 5


# ---- what survives ----

def test_progress_survives_a_restart(tmp_path):
    first = SaveManager(FileStore(tmp_path))
    first.set_high_score(1, 22)
    first.set_best_time(1, 13.2)
    first.add_coins(22)
    first.unlock_achievement("first_blood")
    first.set_audio_settings({"master_volume": 0.4})

    second = SaveManager(FileStore(tmp_path))
    assert second.get_high_score(1) == 22
    assert second.get_best_time(1) == 13.2
    assert second.get_total_coins() == 22
    assert second.has_achievement("first_blood")
    assert second.get_audio_settings()["master_volume"] == 0.4


def test_browser_save_survives_a_reload_even_with_non_ascii_text():
    local = FakeLocalStorage()
    first = SaveManager(BrowserStore(local))
    first.unlock_achievement("café")
    first.add_coins(3)
    assert local.items["shadowmario/save.json"].isascii()

    reloaded = SaveManager(BrowserStore(local))  # same localStorage, fresh page
    assert reloaded.has_achievement("café")
    assert reloaded.get_total_coins() == 3


def test_blocked_browser_storage_still_works_for_the_page():
    store = BrowserStore(BlockedLocalStorage())
    manager = SaveManager(store)
    manager.add_coins(7)
    assert SaveManager(store).get_total_coins() == 7


def test_corrupt_save_is_moved_aside_not_overwritten(tmp_path):
    (tmp_path / SAVE_NAME).write_text('{"total_coins": 34', encoding="utf-8")
    manager = SaveManager(FileStore(tmp_path))
    assert manager.data == default_data()
    manager.add_coins(1)
    assert (tmp_path / "save.json.corrupt").read_text() == '{"total_coins": 34'
    assert json.loads((tmp_path / SAVE_NAME).read_text())["total_coins"] == 1


@pytest.mark.parametrize("text", ['[1, 2]', '{"high_scores": [5, 6]}', '{"unlocked_levels": 3}'])
def test_save_of_the_wrong_shape_falls_back_to_defaults(tmp_path, text):
    (tmp_path / SAVE_NAME).write_text(text, encoding="utf-8")
    manager = SaveManager(FileStore(tmp_path))
    assert manager.data == default_data()
    assert (tmp_path / "save.json.corrupt").read_text() == text


def test_corrupt_browser_save_is_kept_under_another_key():
    local = FakeLocalStorage()
    local.items["shadowmario/save.json"] = "{oops"
    SaveManager(BrowserStore(local))
    assert local.items == {"shadowmario/save.json.corrupt": "{oops"}


def test_legacy_save_beside_the_code_is_adopted_once(tmp_path):
    legacy = tmp_path / "repo" / "save.json"
    legacy.parent.mkdir()
    legacy.write_text(json.dumps({"total_coins": 346, "high_scores": {"1": 40}}), encoding="utf-8")
    data_dir = tmp_path / "data"

    adopted = SaveManager(FileStore(data_dir), legacy_path=legacy)
    assert adopted.get_total_coins() == 346 and adopted.get_high_score(1) == 40
    assert json.loads((data_dir / SAVE_NAME).read_text())["total_coins"] == 346
    assert json.loads(legacy.read_text())["total_coins"] == 346  # left untouched

    adopted.add_coins(4)
    legacy.write_text(json.dumps({"total_coins": 1}), encoding="utf-8")
    later = SaveManager(FileStore(data_dir), legacy_path=legacy)
    assert later.get_total_coins() == 350  # the data-dir save wins once it exists


def test_unreadable_legacy_save_is_ignored(tmp_path):
    legacy = tmp_path / "save.json"
    legacy.write_text("{broken", encoding="utf-8")
    manager = SaveManager(FileStore(tmp_path / "data"), legacy_path=legacy)
    assert manager.data == default_data()
    assert legacy.read_text() == "{broken"
    assert not (tmp_path / "data").exists()


def test_reset_restores_defaults_and_persists(tmp_path):
    manager = SaveManager(FileStore(tmp_path))
    manager.add_coins(9)
    manager.reset()
    assert SaveManager(FileStore(tmp_path)).data == default_data()
