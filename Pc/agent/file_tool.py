# Haven Agent v1 - file_tool.py
# Safe file reading and writing for Haven.
# Rules, so Haven cannot break Joseph's projects by accident:
#  1. Only work inside allowed folders (default: the Haven Pc folder,
#     plus any folder Joseph adds in allowed_folders.txt).
#  2. NEVER touch Model/, venv/, .git/, __pycache__/, build/, .env, or any .env file.
#  3. Before changing a file, make a backup copy in Pc/logs/backups/.
#     If the change goes wrong, the backup can put it back.
#  4. Never delete a file. Only read, create, or edit.

import os
import shutil
import time

# Folders and files Haven must NEVER touch, even if asked
FORBIDDEN_NAMES = {
    "Model", "venv", ".venv", ".git", "__pycache__", "node_modules",
    "build", ".gradle", ".idea", ".junie",
}
FORBIDDEN_FILES = {".env"}
FORBIDDEN_ENDINGS = (".env", ".gguf", ".onnx", ".bin", ".pyc")


def _is_forbidden(path):
    """True if the path goes through a forbidden folder or is a forbidden file."""
    parts = [p.lower() for p in os.path.normpath(str(path)).split(os.sep) if p]
    forbidden_folders = {
        "model", "venv", ".venv", ".git", "__pycache__", "node_modules",
        "build", ".gradle", ".idea", ".junie",
    }
    if any(part in forbidden_folders for part in parts):
        return True
    name = os.path.basename(str(path)).lower()
    if name in FORBIDDEN_FILES or name.endswith(FORBIDDEN_ENDINGS):
        return True
    return False


class FileTool:
    """Read, create and edit files, only in allowed folders, with backups."""

    def __init__(self, allowed_folders=None, log_folder=None):
        # Default allowed folder: the Pc folder this file lives in
        pc_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if allowed_folders is None:
            allowed_folders = [pc_folder]
            # Also read allowed_folders.txt if Joseph made one, one folder per line
            txt = os.path.join(pc_folder, "allowed_folders.txt")
            if os.path.exists(txt):
                with open(txt, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            allowed_folders.append(line)
        self.allowed_folders = [os.path.abspath(f) for f in allowed_folders]
        if log_folder is None:
            log_folder = os.path.join(pc_folder, "logs", "backups")
        self.backup_folder = log_folder
        os.makedirs(self.backup_folder, exist_ok=True)

    def _is_allowed(self, path):
        full = os.path.abspath(str(path))
        if _is_forbidden(full):
            return False
        for folder in self.allowed_folders:
            if full.startswith(folder + os.sep) or full == folder:
                return True
        return False

    def read_file(self, path):
        """Read a text file. Returns the text, or an error message."""
        if not self._is_allowed(path):
            return f"Not allowed: {path}. That folder is not in the allowed list, or it is a forbidden folder like Model or venv."
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Could not read {path}: {e}"

    def backup(self, path):
        """Make a backup copy before changing a file. Returns backup path or ''."""
        try:
            # Include microseconds, so two edits in the same second
            # do not overwrite each other's backup.
            import datetime
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            name = os.path.basename(str(path))
            backup_name = f"{stamp}_{name}.bak"
            backup_path = os.path.join(self.backup_folder, backup_name)
            shutil.copy2(path, backup_path)
            return backup_path
        except Exception:
            return ""

    def write_file(self, path, content):
        """Create or overwrite a file, after making a backup if it already exists."""
        if not self._is_allowed(path):
            return f"Not allowed: {path}"
        try:
            if os.path.exists(path):
                self.backup(path)
            os.makedirs(os.path.dirname(os.path.abspath(str(path))), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Saved {path}"
        except Exception as e:
            return f"Could not save {path}: {e}"

    def edit_file(self, path, old_text, new_text):
        """Replace old_text with new_text in a file, once, with a backup first.

        Fails safely if old_text is not found, or if it appears more than once
        (so Haven does not change the wrong place).
        """
        if not self._is_allowed(path):
            return f"Not allowed: {path}"
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            return f"Could not read {path}: {e}"
        count = content.count(old_text)
        if count == 0:
            return f"Could not find that text in {path}. Nothing was changed."
        if count > 1:
            return f"That text appears {count} times in {path}. Nothing was changed, so Haven does not edit the wrong place."
        self.backup(path)
        content = content.replace(old_text, new_text, 1)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Edited {path}. Backup saved in logs/backups/."
        except Exception as e:
            return f"Could not save {path}: {e}"
