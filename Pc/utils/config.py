# File: utils/config.py

import json
import os
from typing import Any, Dict, Optional

class Config:
    """
    Global configuration handler for Haven.
    Loads and saves settings from a JSON file.
    Safe on Windows, Linux, and NAS environments.
    """

    def __init__(self, path: str = "data/config.json"):
        self.path = path
        self.data: Dict[str, Any] = {}
        self._ensure_storage()
        self.load()

    # -----------------------------
    # Internal Helpers
    # -----------------------------

    def _ensure_storage(self):
        """Ensure the config directory and file exist."""
        folder = os.path.dirname(self.path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)

        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump({}, f, indent=4)

    # -----------------------------
    # Load / Save
    # -----------------------------

    def load(self):
        """Load config from JSON file."""
        try:
            with open(self.path, "r") as f:
                self.data = json.load(f)
        except Exception:
            self.data = {}

    def save(self):
        """Save config to JSON file."""
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4)

    # -----------------------------
    # Public API
    # -----------------------------

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a config value safely."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value and save."""
        self.data[key] = value
        self.save()

    def delete(self, key: str) -> bool:
        """Delete a config key."""
        if key in self.data:
            del self.data[key]
            self.save()
            return True
        return False

    def all(self) -> Dict[str, Any]:
        """Return all config values."""
        return self.data.copy()
