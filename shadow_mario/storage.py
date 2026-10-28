"""Where the game keeps data between sessions.

Desktop: one file per name in the user's data folder (the OS convention, or
$SHADOW_MARIO_DATA_DIR), each write atomic. Browser (pygbag): window.localStorage.
Files written in the browser land in an in-memory filesystem that is gone on
the next page load, which is how every save on the itch.io build was lost on
reload until October 2026.
"""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

APP_DIR_NAME = "ShadowMario"
DATA_DIR_ENV = "SHADOW_MARIO_DATA_DIR"
BROWSER_KEY_PREFIX = "shadowmario/"
# Where the save lived before October 2026: next to the code. It also got
# packaged into the April 2026 web build that way.
LEGACY_SAVE_PATH = Path(__file__).resolve().parent.parent / "save.json"


class Store(Protocol):
    def read(self, name: str) -> str | None: ...

    def write(self, name: str, text: str) -> None: ...

    def quarantine(self, name: str) -> None: ...


def is_browser() -> bool:
    return sys.platform == "emscripten"


def user_data_dir(
    env: Mapping[str, str] | None = None,
    platform_name: str | None = None,
    home: str | os.PathLike | None = None,
) -> Path:
    """Per-user data folder for this game."""
    env = os.environ if env is None else env
    platform_name = sys.platform if platform_name is None else platform_name
    home = Path.home() if home is None else Path(home)
    override = env.get(DATA_DIR_ENV)
    if override:
        return Path(override)
    if platform_name == "darwin":
        return home / "Library" / "Application Support" / APP_DIR_NAME
    if platform_name.startswith("win"):
        return Path(env.get("APPDATA") or home / "AppData" / "Roaming") / APP_DIR_NAME
    return Path(env.get("XDG_DATA_HOME") or home / ".local" / "share") / "shadow-mario"


class FileStore:
    """One file per name in a folder.

    A write goes to a temporary file in the same folder and replaces the old
    file only once it is completely on disk, so a crash or a full disk mid-write
    leaves the previous version intact instead of a truncated one.
    """

    def __init__(self, directory: str | os.PathLike) -> None:
        self.directory = Path(directory)

    def path(self, name: str) -> Path:
        return self.directory / name

    def read(self, name: str) -> str | None:
        try:
            data = self.path(name).read_bytes()
        except OSError:
            return None
        # Undecodable bytes must not read as "no save": the caller would then
        # overwrite them. Replacement characters make the JSON fail to parse,
        # and the caller quarantines the original file.
        return data.decode("utf-8", errors="replace")

    def write(self, name: str, text: str) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.directory, prefix=f".{name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path(name))
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
            raise

    def quarantine(self, name: str) -> None:
        """Move an unreadable file aside, byte for byte, so nothing overwrites it."""
        with contextlib.suppress(OSError):
            os.replace(self.path(name), self.path(name + ".corrupt"))


class BrowserStore:
    """window.localStorage through pygbag's JavaScript bridge.

    A missing key reads as None. Storage can be refused outright (private
    browsing, third-party storage blocked for the itch.io frame) or full; then
    values are kept in memory for the rest of the page instead of failing.
    Errors raised from JavaScript arrive as plain exceptions, hence the broad
    catches.
    """

    def __init__(self, local_storage, prefix: str = BROWSER_KEY_PREFIX) -> None:
        self._storage = local_storage
        self._prefix = prefix
        self._memory: dict[str, str] = {}

    def read(self, name: str) -> str | None:
        try:
            value = self._storage.getItem(self._prefix + name)
        except Exception:
            value = None
        if value is None:
            return self._memory.get(name)
        return str(value)

    def write(self, name: str, text: str) -> None:
        self._memory[name] = text
        with contextlib.suppress(Exception):
            self._storage.setItem(self._prefix + name, text)

    def quarantine(self, name: str) -> None:
        text = self.read(name)
        self._memory.pop(name, None)
        if text is None:
            return
        self.write(name + ".corrupt", text)
        with contextlib.suppress(Exception):
            self._storage.removeItem(self._prefix + name)


def default_store() -> Store:
    """localStorage in the browser, the user's data folder on desktop."""
    if is_browser():
        import platform  # pygbag adds `window` to this stdlib module in the browser

        try:
            local_storage = platform.window.localStorage
        except Exception:
            local_storage = None
        return BrowserStore(local_storage)
    return FileStore(user_data_dir())
