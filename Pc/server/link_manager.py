# File: server/link_manager.py

import json
import os
from typing import Dict, Optional

class LinkManager:
    """
    Handles loading, saving, and updating link paths for Haven.
    This is used for your Master Links folder system.
    """

    def __init__(self, storage_path: str = "data/links.json"):
        self.storage_path = storage_path
        self.links: Dict[str, str] = {}
        self._ensure_storage()
        self.load_links()

    # -----------------------------
    # Internal Helpers
    # -----------------------------

    def _ensure_storage(self):
        """Make sure the directory exists."""
        folder = os.path.dirname(self.storage_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)

        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w") as f:
                json.dump({}, f, indent=4)

    # -----------------------------
    # Load / Save
    # -----------------------------

    def load_links(self):
        """Load links from JSON file."""
        try:
            with open(self.storage_path, "r") as f:
                self.links = json.load(f)
        except Exception:
            self.links = {}

    def save_links(self):
        """Save links to JSON file."""
        with open(self.storage_path, "w") as f:
            json.dump(self.links, f, indent=4)

    # -----------------------------
    # Public API
    # -----------------------------

    def get_link(self, name: str) -> Optional[str]:
        """Return a link path by name."""
        return self.links.get(name)

    def set_link(self, name: str, path: str) -> bool:
        """
        Add or update a link.
        Returns True if successful.
        """
        if not isinstance(name, str) or not isinstance(path, str):
            return False

        self.links[name] = path
        self.save_links()
        return True

    def delete_link(self, name: str) -> bool:
        """Remove a link by name."""
        if name in self.links:
            del self.links[name]
            self.save_links()
            return True
        return False

    def list_links(self) -> Dict[str, str]:
        """Return all stored links."""
        return self.links.copy()
