# Haven Agent v1 - code_tool.py
# Propose a code change, show Joseph what it will do, then apply it only
# after approval. After editing a Python file, check it still works
# (py_compile). If it does not compile, put the backup back.

import os
import py_compile
import shutil

from file_tool import FileTool
from activity_log import ActivityLog


class CodeTool:
    """Propose and apply code edits, safely."""

    def __init__(self, allowed_folders=None, log_folder=None):
        self.files = FileTool(allowed_folders=allowed_folders)
        self.log = ActivityLog(log_folder=log_folder)

    def propose_edit(self, path, old_text, new_text, reason=""):
        """Show what would change, without changing anything yet.

        Returns a plain-text preview Joseph can read and approve.
        """
        content = self.files.read_file(path)
        if content.startswith("Could not") or content.startswith("Not allowed"):
            return content
        if old_text not in content:
            return f"Could not find that text in {path}. Nothing was changed."
        preview = (
            f"Fix for: {path}\n"
            f"Reason: {reason}\n\n"
            f"--- old ---\n{old_text}\n\n"
            f"--- new ---\n{new_text}\n"
        )
        return preview

    def apply_edit(self, path, old_text, new_text, reason=""):
        """Apply an approved edit. Backup first, compile-check Python files."""
        # Find the backup that edit_file() just made, so we can restore it
        backup_folder = self.files.backup_folder
        before = set(os.listdir(backup_folder)) if os.path.exists(backup_folder) else set()

        result = self.files.edit_file(path, old_text, new_text)
        if "Edited" not in result:
            self.log.log("edit_failed", path, reason + " | " + result, "failed")
            return result

        # If it is a Python file, check it still compiles
        if str(path).lower().endswith(".py"):
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as e:
                # It broke - put the backup back
                after = set(os.listdir(backup_folder)) if os.path.exists(backup_folder) else set()
                new_backups = sorted(after - before)
                if new_backups:
                    backup_path = os.path.join(backup_folder, new_backups[-1])
                    shutil.copy2(backup_path, path)
                    self.log.log("edit_reverted", path, f"Compile failed, backup restored: {e}", "failed")
                    return f"That edit broke {path} ({e}). I put the backup back, nothing was changed."
                self.log.log("edit_failed", path, f"Compile failed: {e}", "failed")
                return f"That edit broke {path} ({e}). Please check the file."

        self.log.log("edit_applied", path, reason, "ok")
        return result + f"\nReason: {reason}"
