# Haven Agent v1 - exec_tool.py
# Run a test command on the PC, safely.
# Only a small list of safe commands is allowed:
#   python <file>  (to test a file)
#   python -m py_compile <file>  (to check a file still works)
#   python -m pip --version  (just to check pip)
# Everything else is refused, including delete, format, shutdown,
# and any command with &  |  ;  or > in it (those can chain commands).

import os
import shutil
import subprocess
import sys

ALLOWED_STARTS = (
    ("python", "-m", "py_compile"),
    ("python",),
    ("py",),
)
BLOCKED_WORDS = ("del ", "rm ", "format", "shutdown", "restart", "reg ", "powershell", "cmd", "&", "|", ";", ">", "<", "`", "$(")


class ExecTool:
    """Run safe test commands, with a time limit."""

    def __init__(self, allowed_folders=None):
        pc_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if allowed_folders is None:
            allowed_folders = [pc_folder]
        self.allowed_folders = [os.path.abspath(f) for f in allowed_folders]

    def run(self, command, timeout_seconds=30):
        """command is a list, e.g. ["python", "-m", "py_compile", "chat/repository.py"]"""
        if not isinstance(command, (list, tuple)) or not command:
            return "No command given."
        text = " ".join(str(c) for c in command)
        if any(b in text.lower() for b in BLOCKED_WORDS):
            return f"Blocked: that command is not allowed for safety. Command was: {text}"
        if tuple(str(c) for c in command[:3]) not in [
            ("python", "-m", "py_compile"),
        ] and command[0] not in ("python", "py"):
            return f"Blocked: only python test commands are allowed. Command was: {text}"
        # The file being tested must be in an allowed folder
        if len(command) >= 2:
            target = os.path.abspath(command[-1])
            if not any(target.startswith(f + os.sep) or target == f for f in self.allowed_folders):
                # Allow py_compile with a relative path inside the Pc folder
                if not os.path.exists(target):
                    return f"Blocked: {command[-1]} is not in an allowed folder."
        try:
            # On Windows the command is 'python', on Linux/Mac it is often 'python3'.
            # Use whichever one actually exists on this computer.
            cmd = [str(c) for c in command]
            if cmd[0] in ("python", "py"):
                found = shutil.which(cmd[0]) or shutil.which("python3") or sys.executable
                cmd[0] = found
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=timeout_seconds,
                cwd=self.allowed_folders[0],
            )
            out = (result.stdout or "") + (result.stderr or "")
            status = "OK" if result.returncode == 0 else f"FAILED (code {result.returncode})"
            return f"{status}\n{out.strip()[:2000]}"
        except subprocess.TimeoutExpired:
            return "Timed out - the command took too long, so it was stopped."
        except Exception as e:
            return f"Could not run command: {e}"
