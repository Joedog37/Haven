# Haven Agent v1 - approval.py
# Every change Haven wants to make must be approved first.
# This is the safety switch Joseph asked for: Haven proposes, Joseph says yes/no.
# Nothing is applied until approve() is called.
# A kill switch turns the whole agent off instantly.

import json
import os
import time


class ApprovalManager:
    """Keep a list of things Haven wants to do, waiting for Joseph."""

    def __init__(self, log_folder=None):
        if log_folder is None:
            # Pc/logs, next to the other Haven logs
            log_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
        self.log_folder = log_folder
        os.makedirs(self.log_folder, exist_ok=True)
        self.file_path = os.path.join(self.log_folder, "agent_approvals.json")
        self.enabled = True  # kill switch: False = agent is off, chat still works
        self.requests = self._load()

    def _load(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.requests, f, indent=2)

    def disable(self):
        """Kill switch - turn the agent off. Chat still works."""
        self.enabled = False
        return "Agent is OFF. Haven can still chat, but she cannot change any files."

    def enable(self):
        self.enabled = True
        return "Agent is ON. Haven can propose changes again."

    def propose(self, action, file_path, description, preview=""):
        """Haven asks: 'Can I do this?' Returns the request id."""
        if not self.enabled:
            return None
        request = {
            "id": len(self.requests) + 1,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,          # e.g. "edit_file", "create_file", "run_test"
            "file": str(file_path),
            "description": description,
            "preview": preview[:2000],  # first 2000 chars, so Joseph can see it
            "status": "waiting",        # waiting / approved / denied
        }
        self.requests.append(request)
        self._save()
        return request["id"]

    def list_waiting(self):
        return [r for r in self.requests if r["status"] == "waiting"]

    def approve(self, request_id):
        """Joseph says yes. Returns the request, or None if not found."""
        for r in self.requests:
            if r["id"] == request_id and r["status"] == "waiting":
                r["status"] = "approved"
                self._save()
                return r
        return None

    def deny(self, request_id):
        """Joseph says no. The change is NOT made, but it is logged."""
        for r in self.requests:
            if r["id"] == request_id and r["status"] == "waiting":
                r["status"] = "denied"
                self._save()
                return r
        return None

    def get_status(self):
        return {
            "enabled": self.enabled,
            "waiting": len(self.list_waiting()),
            "total": len(self.requests),
        }
