# File: utils/paths.py

import os
from typing import Optional

class Paths:
    """
    Utility class for safe path handling across Windows and Linux.
    Haven uses this to normalize, validate, and create directories.
    """

    @staticmethod
    def normalize(path: str) -> str:
        """
        Normalize a path to the current OS format.
        Converts slashes and expands ~.
        """
        if not isinstance(path, str):
            return path

        # Expand ~ to user home
        path = os.path.expanduser(path)

        # Normalize slashes and remove weird characters
        return os.path.normpath(path)

    @staticmethod
    def exists(path: str) -> bool:
        """Check if a file or folder exists."""
        return os.path.exists(Paths.normalize(path))

    @staticmethod
    def ensure_folder(path: str) -> str:
        """
        Ensure a folder exists. If not, create it.
        Returns the normalized path.
        """
        path = Paths.normalize(path)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @staticmethod
    def join(*parts: str) -> str:
        """
        Safely join multiple path parts.
        Example:
            Paths.join("data", "memory", "user.json")
        """
        return Paths.normalize(os.path.join(*parts))

    @staticmethod
    def filename(path: str) -> str:
        """Return the filename from a path."""
        return os.path.basename(Paths.normalize(path))

    @staticmethod
    def parent(path: str) -> str:
        """Return the parent directory of a path."""
        return Paths.normalize(os.path.dirname(Paths.normalize(path)))

    @staticmethod
    def is_file(path: str) -> bool:
        """Check if path is a file."""
        return os.path.isfile(Paths.normalize(path))

    @staticmethod
    def is_folder(path: str) -> bool:
        """Check if path is a folder."""
        return os.path.isdir(Paths.normalize(path))
