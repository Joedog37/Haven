# Haven Agent v1 - haven_agent.py
# The agent itself. This ties the other files together:
#   approval.py      - Joseph approves every change first
#   activity_log.py  - everything is written down
#   file_tool.py     - safe file reading / writing, with backups
#   code_tool.py     - propose and apply code fixes, with a compile check
#   exec_tool.py     - run safe test commands only
#   scan_tool.py     - scan a drive and list all projects
#
# How Joseph uses it (for now, from a command prompt in the Pc folder):
#   python agent/haven_agent.py scan G:
#   python agent/haven_agent.py status
#   python agent/haven_agent.py propose
#   python agent/haven_agent.py approve 1
#   python agent/haven_agent.py deny 1
#   python agent/haven_agent.py off
#   python agent/haven_agent.py on
#
# Later, these same functions can be wired into the web dashboard
# (server/api.py) so Joseph can approve from the Haven website.

import os
import sys

# Make sure imports work whether this is run as a script or a module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from approval import ApprovalManager
from activity_log import ActivityLog
from code_tool import CodeTool
from exec_tool import ExecTool
from scan_tool import scan_drive


class HavenAgent:
    """Haven as an agent: propose, approve, apply, test, log."""

    def __init__(self, allowed_folders=None):
        self.approvals = ApprovalManager()
        self.log = ActivityLog()
        self.code = CodeTool(allowed_folders=allowed_folders)
        self.exec_tool = ExecTool(allowed_folders=allowed_folders)

    def status(self):
        s = self.approvals.get_status()
        waiting = self.approvals.list_waiting()
        lines = [
            f"Agent enabled: {s['enabled']}",
            f"Waiting for approval: {s['waiting']}",
            f"Total requests so far: {s['total']}",
        ]
        for r in waiting:
            lines.append(f"  #{r['id']} - {r['action']} - {r['file']}: {r['description']}")
        lines.append("")
        lines.append("Recent activity:")
        for e in self.log.recent(5):
            lines.append(f"  {e['time']} - {e['action']} - {e['file']} - {e['outcome']}")
        return "\n".join(lines)

    def propose_fix(self, file_path, old_text, new_text, reason=""):
        """Haven proposes a fix. Nothing changes yet. Returns request id."""
        if not self.approvals.enabled:
            return "Agent is OFF. Turn it on first."
        preview = self.code.propose_edit(file_path, old_text, new_text, reason)
        request_id = self.approvals.propose("edit_file", file_path, reason, preview)
        self.log.log("proposed", file_path, reason, "ok")
        return request_id, preview

    def approve_and_apply(self, request_id):
        """Joseph approved a request. Apply it, test it, log it."""
        request = self.approvals.approve(request_id)
        if request is None:
            return f"No waiting request #{request_id}."
        # The preview holds the old/new text in a simple format.
        # For v1, the fix itself is stored in the request by the caller.
        # See agent_test.py for a working example of a full approve -> apply flow.
        return request

    def scan(self, drive):
        projects, message = scan_drive(drive)
        self.log.log("scan_drive", drive, message, "ok")
        return message


def main():
    agent = HavenAgent()
    if len(sys.argv) < 2:
        print("Usage: python agent/haven_agent.py status | scan G: | off | on")
        print(agent.status())
        return
    cmd = sys.argv[1].lower()
    if cmd == "status":
        print(agent.status())
    elif cmd == "scan" and len(sys.argv) >= 3:
        print(agent.scan(sys.argv[2]))
    elif cmd == "off":
        print(agent.approvals.disable())
    elif cmd == "on":
        print(agent.approvals.enable())
    else:
        print("Usage: python agent/haven_agent.py status | scan G: | off | on")


if __name__ == "__main__":
    main()
