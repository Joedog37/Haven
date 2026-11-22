# Haven Agent v1 - agent_test.py
# Run this in the Pc folder to test that the agent works, safely.
#   python agent_test.py
# It does NOT change any real Haven files. It makes a small test file
# in a temp folder, proposes a fix, approves it, applies it, and checks
# that the backup was made. If it prints "ALL TESTS PASSED", the agent is ready.

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent"))

from approval import ApprovalManager
from code_tool import CodeTool
from exec_tool import ExecTool
from scan_tool import scan_drive


def main():
    print("Haven Agent v1 - test")
    print("=" * 40)
    tmp = tempfile.mkdtemp()
    test_file = os.path.join(tmp, "test_fix.py")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write('print("hello")\n# TODO: fix this line\n')

    # 1. Approval
    approvals = ApprovalManager(log_folder=tmp)
    rid = approvals.propose("edit_file", test_file, "Test fix", "old -> new")
    assert rid == 1, "propose failed"
    assert len(approvals.list_waiting()) == 1, "waiting list failed"
    print("1. Approval: propose + list waiting - OK")

    # 2. CodeTool - propose, approve, apply
    code = CodeTool(allowed_folders=[tmp], log_folder=tmp)
    preview = code.propose_edit(test_file, "# TODO: fix this line", "# fixed", "Test fix")
    assert "old" in preview, "preview failed"
    approvals.approve(rid)
    result = code.apply_edit(test_file, "# TODO: fix this line", "# fixed", "Test fix")
    assert "Edited" in result, f"apply failed: {result}"
    with open(test_file, "r", encoding="utf-8") as f:
        assert "# fixed" in f.read(), "edit did not stick"
    print("2. CodeTool: propose + approve + apply - OK")

    # 3. Backup was made
    backups = os.listdir(code.files.backup_folder)
    assert backups, "no backup was made"
    print(f"3. Backup: made {backups[0]} - OK")

    # 4. A broken edit is reverted
    bad = code.apply_edit(test_file, "# fixed", "def broken(:", "Bad edit test")
    assert "backup back" in bad or "broke" in bad, f"broken edit was not reverted: {bad}"
    with open(test_file, "r", encoding="utf-8") as f:
        assert "# fixed" in f.read(), "broken edit was not reverted"
    print("4. Broken edit: reverted from backup - OK")

    # 5. Forbidden folders are refused
    forbidden = code.files.write_file(os.path.join(tmp, "Model", "test.py"), "x")
    # Model is forbidden even inside the allowed folder
    assert "Not allowed" in forbidden, f"forbidden folder was not blocked: {forbidden}"
    print("5. Forbidden folders (Model/venv/.git): blocked - OK")

    # 6. ExecTool - only safe python commands
    exec_tool = ExecTool(allowed_folders=[tmp])
    out = exec_tool.run(["python", "-m", "py_compile", test_file])
    assert "OK" in out, f"exec failed: {out}"
    blocked = exec_tool.run(["del", "test.py"])
    assert "Blocked" in blocked, "dangerous command was not blocked"
    print("6. ExecTool: safe command OK, dangerous command blocked - OK")

    # 7. ScanTool - finds a project folder
    proj = os.path.join(tmp, "MyTestProject")
    os.makedirs(proj, exist_ok=True)
    with open(os.path.join(proj, "README.md"), "w", encoding="utf-8") as f:
        f.write("# test\n")
    projects, msg = scan_drive(tmp, log_folder=tmp)
    names = [p["name"] for p in projects]
    assert "MyTestProject" in names, f"scan did not find project: {names}"
    print("7. ScanTool: found MyTestProject - OK")

    print("=" * 40)
    print("ALL TESTS PASSED - the agent is ready to use.")
    print(f"Test folder (safe to delete): {tmp}")


if __name__ == "__main__":
    main()
