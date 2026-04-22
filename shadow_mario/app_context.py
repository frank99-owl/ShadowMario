"""Application-wide service context for dependency injection."""

from dataclasses import dataclass

from .audio import AudioManager, get_audio_manager
from .config import GameConfig
from .runtime_config import RuntimeConfig, get_runtime_config
from .save import SaveManager, get_save_manager


@dataclass(frozen=True)
class AppContext:
    """Container for shared runtime services."""

    config: GameConfig
    save: SaveManager
    audio: AudioManager
    runtime_config: RuntimeConfig


def hydrate_audio_settings(save: SaveManager, audio: AudioManager) -> None:
    """Load persisted audio settings into the audio manager."""
    audio.load_settings(save.get_audio_settings())


def build_app_context() -> AppContext:
    """Build and initialize the shared application context."""
    config = GameConfig()
    save = get_save_manager()
    audio = get_audio_manager()
    runtime_config = get_runtime_config()
    hydrate_audio_settings(save, audio)
    return AppContext(
        config=config,
        save=save,
        audio=audio,
        runtime_config=runtime_config,
    )
