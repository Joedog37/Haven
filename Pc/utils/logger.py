# File: utils/logger.py

import os
import datetime
from typing import Optional

class Logger:
    """
    Simple daily log writer for Haven.
    Creates a new log file each day and appends messages safely.
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self._ensure_folder()

    # -----------------------------
    # Internal Helpers
    # -----------------------------

    def _ensure_folder(self):
        """Ensure the log directory exists."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _get_log_path(self) -> str:
        """Return today's log file path."""
        today = datetime.date.today().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"{today}.log")

    # -----------------------------
    # Public API
    # -----------------------------

    def write(self, message: str, tag: Optional[str] = None):
        """
        Write a timestamped log entry.
        Example:
            logger.write("Haven started")
            logger.write("User said hello", tag="USER")
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        tag_text = f"[{tag}]" if tag else ""
        line = f"[{timestamp}] {tag_text} {message}\n"

        try:
            with open(self._get_log_path(), "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            # Fail silently — logging should never crash Haven
            pass

    def info(self, message: str):
        self.write(message, tag="INFO")

    def warn(self, message: str):
        self.write(message, tag="WARN")

    def error(self, message: str):
        self.write(message, tag="ERROR")

    def debug(self, message: str):
        self.write(message, tag="DEBUG")
