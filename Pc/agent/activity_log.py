# Haven Agent v1 - activity_log.py
# Write down everything the agent does, so Joseph can check it later.
# If something goes wrong, this log shows what file changed, when, and why.

import json
import os
import time


class ActivityLog:
    """Simple append-only log for agent actions."""

    def __init__(self, log_folder=None):
        if log_folder is None:
            log_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
        self.log_folder = log_folder
        os.makedirs(self.log_folder, exist_ok=True)
        self.file_path = os.path.join(self.log_folder, "agent_activity.json")

    def log(self, action, file_path="", description="", outcome="ok"):
        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "file": str(file_path),
            "description": description,
            "outcome": outcome,
        }
        entries = []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                entries = json.load(f)
                if not isinstance(entries, list):
                    entries = []
        except Exception:
            entries = []
        entries.append(entry)
        # Keep the last 500 entries, so the file does not grow forever
        entries = entries[-500:]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
        return entry

    def recent(self, count=20):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                entries = json.load(f)
                return entries[-count:]
        except Exception:
            return []
