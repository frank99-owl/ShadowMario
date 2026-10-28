import json
import os
from typing import Dict, Any



class RuntimeConfig:
    """Runtime JSON configuration loader.

    Manages UI colors, sizes and other runtime-adjustable parameters.
    Independent of app.properties compile-time configuration.
    """

    _instance: "RuntimeConfig | None" = None

    def __new__(cls) -> "RuntimeConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "res", "runtime_config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            self._data: Dict[str, Any] = json.load(f)

        self.colors = self._data.get("colors", {})
        self.ui = self._data.get("ui", {})

    def color(self, name: str) -> tuple:
        """Get color configuration, supports RGB and RGBA."""
        c = self.colors.get(name, [255, 255, 255])
        return tuple(c)

    def ui_value(self, name: str, default: Any = 0) -> Any:
        """Get UI value configuration."""
        return self.ui.get(name, default)

    def save(self, filepath: str | None = None) -> None:
        """Save current configuration to file."""
        if filepath is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            filepath = os.path.join(base_dir, "res", "runtime_config.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)


# Convenience function, returns singleton instance
def get_runtime_config() -> RuntimeConfig:
    return RuntimeConfig()
