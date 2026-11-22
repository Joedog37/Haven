# File system tools - search, open, manage files
import os
import subprocess
import platform


class FileSystemTools:
    """File system operations for Haven."""

    def __init__(self):
        self.os_name = platform.system()

    def search_files(self, query: str, directory: str = None, max_results: int = 10) -> str:
        """Search for files by name in a directory."""
        try:
            if directory is None:
                # Search in user's home directory
                directory = os.path.expanduser("~")

            if not os.path.isdir(directory):
                return f"Directory not found: {directory}"

            results = []
            query_lower = query.lower()

            for root, dirs, files in os.walk(directory):
                # Skip hidden and system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv')]
                for file in files:
                    if query_lower in file.lower() and len(results) < max_results:
                        full_path = os.path.join(root, file)
                        results.append(full_path)

            if results:
                lines = [f"Found {len(results)} file(s) matching '{query}':"]
                for path in results:
                    # Make relative to home for readability
                    try:
                        rel = os.path.relpath(path, os.path.expanduser("~"))
                        lines.append(f"  ~\\{rel}")
                    except ValueError:
                        lines.append(f"  {path}")
                return "\n".join(lines)
            else:
                return f"No files found matching '{query}' in {directory}"
        except Exception as e:
            return f"Search failed: {e}"

    def open_file(self, file_path: str) -> str:
        """Open a file with the default application."""
        try:
            # Try to resolve relative paths
            if not os.path.isabs(file_path):
                possible = [
                    os.path.join(os.path.expanduser("~"), file_path),
                    os.path.join(os.getcwd(), file_path),
                ]
                for p in possible:
                    if os.path.exists(p):
                        file_path = p
                        break

            if not os.path.exists(file_path):
                return f"File not found: {file_path}"

            if self.os_name == "Windows":
                os.startfile(file_path)
            elif self.os_name == "Darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["xdg-open", file_path])

            return f"Opening {os.path.basename(file_path)}..."
        except Exception as e:
            return f"Could not open file: {e}"

    def open_folder(self, folder_path: str) -> str:
        """Open a folder in the file explorer."""
        try:
            if not os.path.isabs(folder_path):
                folder_path = os.path.join(os.path.expanduser("~"), folder_path)

            if not os.path.isdir(folder_path):
                return f"Folder not found: {folder_path}"

            if self.os_name == "Windows":
                os.startfile(folder_path)
            elif self.os_name == "Darwin":
                subprocess.run(["open", folder_path])
            else:
                subprocess.run(["xdg-open", folder_path])

            return f"Opening folder: {os.path.basename(folder_path)}"
        except Exception as e:
            return f"Could not open folder: {e}"

    def get_folder_contents(self, folder_path: str, max_items: int = 20) -> str:
        """List contents of a folder."""
        try:
            if not os.path.isabs(folder_path):
                folder_path = os.path.join(os.path.expanduser("~"), folder_path)

            if not os.path.isdir(folder_path):
                return f"Folder not found: {folder_path}"

            items = os.listdir(folder_path)[:max_items]
            dirs = []
            files = []
            for item in items:
                full = os.path.join(folder_path, item)
                if os.path.isdir(full):
                    dirs.append(f"  📁 {item}/")
                else:
                    files.append(f"  📄 {item}")

            result = f"Contents of {os.path.basename(folder_path)}:\n"
            if dirs:
                result += "\n".join(dirs) + "\n"
            if files:
                result += "\n".join(files)

            total = len(os.listdir(folder_path))
            if total > max_items:
                result += f"\n... and {total - max_items} more items"

            return result
        except Exception as e:
            return f"Could not list folder: {e}"

    def get_file_info(self, file_path: str) -> str:
        """Get information about a file."""
        try:
            if not os.path.isabs(file_path):
                file_path = os.path.join(os.path.expanduser("~"), file_path)

            if not os.path.exists(file_path):
                return f"File not found: {file_path}"

            stat = os.stat(file_path)
            size = stat.st_size
            if size > 1024 * 1024 * 1024:
                size_str = f"{size / (1024**3):.1f} GB"
            elif size > 1024 * 1024:
                size_str = f"{size / (1024**2):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} bytes"

            import datetime
            modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

            return f"File: {os.path.basename(file_path)}\nSize: {size_str}\nModified: {modified}\nPath: {file_path}"
        except Exception as e:
            return f"Could not get file info: {e}"

    def get_disk_usage(self) -> str:
        """Get disk usage information."""
        try:
            import psutil
            disk = psutil.disk_usage("/")
            total_gb = disk.total / (1024**3)
            used_gb = disk.used / (1024**3)
            free_gb = disk.free / (1024**3)

            return f"Disk usage:\n  Total: {total_gb:.1f} GB\n  Used: {used_gb:.1f} GB ({disk.percent}%)\n  Free: {free_gb:.1f} GB"
        except Exception as e:
            return f"Could not get disk usage: {e}"

    def get_status(self) -> dict:
        """Return status of file system tools."""
        return {
            "os": self.os_name,
            "search": True,
            "open": True,
            "info": True,
        }
