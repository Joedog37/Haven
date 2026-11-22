# Haven Agent v1 - scan_tool.py
# Scan a drive or folder and make a list of all the projects on it.
# This is for Joseph's question: "is there a way to scan my SSD / external drive?"
# Usage: scan_drive("G:") or scan_drive("E:") or scan_drive("C:\\Users\\Joseph\\Projects")
# It skips the huge folders (Model, venv, .git, node_modules, build, etc.)
# and saves the list to Pc/logs/project_scan.txt and project_scan.json
# Joseph can then send that small text file to his assistant to read.

import json
import os
import time

SKIP_FOLDERS = {
    "model", "venv", ".venv", ".git", "__pycache__", "node_modules",
    "build", ".gradle", ".idea", ".junie", "bin", "obj", ".vs", "dist",
}

# A folder looks like a project if it has one of these files in it
PROJECT_MARKERS = {
    "main.py", "README.md", "README.txt", "requirements.txt",
    "package.json", "build.gradle", "build.gradle.kts", "settings.gradle",
    "Cargo.toml", "go.mod", "pom.xml", ".gitignore",
}


def _folder_size(path, max_files=2000):
    total = 0
    count = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_FOLDERS]
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass
            count += 1
            if count > max_files:
                return total, count
    return total, count


def scan_drive(drive, log_folder=None):
    """Scan a drive letter or folder. Returns a list of projects found."""
    drive = os.path.abspath(drive)
    if not os.path.isdir(drive):
        return [], f"Drive or folder not found: {drive}"

    projects = []
    for root, dirs, files in os.walk(drive):
        # Skip huge / system folders
        dirs[:] = [d for d in dirs if d.lower() not in SKIP_FOLDERS]
        # Skip Windows folders, if scanning a whole drive
        if root.lower() in (drive.lower(),):
            dirs[:] = [d for d in dirs if d.lower() not in ("windows", "program files", "program files (x86)", "programdata")]
        lower_files = {f.lower() for f in files}
        markers_found = lower_files & {m.lower() for m in PROJECT_MARKERS}
        if markers_found:
            size, count = _folder_size(root)
            try:
                modified = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(root)))
            except Exception:
                modified = ""
            projects.append({
                "name": os.path.basename(root),
                "path": root,
                "size_mb": round(size / (1024 * 1024), 1),
                "files": count,
                "last_changed": modified,
                "markers": sorted(markers_found),
            })
            # Do not go deeper inside a project folder - it is one project
            dirs[:] = []

    # Save the list
    if log_folder is None:
        log_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_folder, exist_ok=True)
    txt_path = os.path.join(log_folder, "project_scan.txt")
    json_path = os.path.join(log_folder, "project_scan.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Project scan of {drive}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Projects found: {len(projects)}\n\n")
        for p in sorted(projects, key=lambda x: x["name"].lower()):
            f.write(f"{p['name']} - {p['size_mb']} MB, {p['files']} files, last changed {p['last_changed']}\n")
            f.write(f"  {p['path']}\n")
            f.write(f"  Markers: {', '.join(p['markers'])}\n\n")
    return projects, f"Found {len(projects)} projects on {drive}. List saved to {txt_path}"
