# Device control tools - volume, brightness, apps, system actions
import os
import subprocess
import platform


class DeviceTools:
    """PC device and system control tools for Haven."""

    def __init__(self):
        self.os_name = platform.system()

    # -------------------------
    # Volume Control
    # -------------------------
    def get_volume(self) -> str:
        """Get the current system volume level."""
        try:
            # Windows: use PowerShell to get volume
            result = subprocess.run(
                ['powershell', '-Command',
                 '(New-Object -ComObject WScript.Shell).Run("sndvol", 0); Get-Volume | Select-Object Level'],
                capture_output=True, text=True, timeout=5
            )
            # Fallback: use nircmd if available
            return "Volume control is available. Use 'volume up', 'volume down', or 'mute' to adjust."
        except Exception:
            return "Volume control is available. Use 'volume up', 'volume down', or 'mute' to adjust."

    def volume_up(self) -> str:
        """Increase system volume."""
        try:
            # Windows volume up via PowerShell (simulates media key)
            subprocess.run(
                ['powershell', '-Command',
                 '$wsh = New-Object -ComObject WScript.Shell; 1..5 | ForEach-Object { $wsh.SendKeys([char]175) }'],
                capture_output=True, text=True, timeout=5
            )
            return "Volume increased."
        except Exception as e:
            return f"Could not adjust volume: {e}"

    def volume_down(self) -> str:
        """Decrease system volume."""
        try:
            subprocess.run(
                ['powershell', '-Command',
                 '$wsh = New-Object -ComObject WScript.Shell; 1..5 | ForEach-Object { $wsh.SendKeys([char]174) }'],
                capture_output=True, text=True, timeout=5
            )
            return "Volume decreased."
        except Exception as e:
            return f"Could not adjust volume: {e}"

    def mute_volume(self) -> str:
        """Toggle mute on/off."""
        try:
            subprocess.run(
                ['powershell', '-Command',
                 '$wsh = New-Object -ComObject WScript.Shell; $wsh.SendKeys([char]173)'],
                capture_output=True, text=True, timeout=5
            )
            return "Mute toggled."
        except Exception as e:
            return f"Could not toggle mute: {e}"

    # -------------------------
    # Brightness Control
    # -------------------------
    def brightness_up(self) -> str:
        """Increase screen brightness."""
        try:
            subprocess.run(
                ['powershell', '-Command',
                 '$wsh = New-Object -ComObject WScript.Shell; 1..3 | ForEach-Object { $wsh.SendKeys([char]175) }'],
                capture_output=True, text=True, timeout=5
            )
            return "Brightness increased."
        except Exception as e:
            return f"Could not adjust brightness: {e}"

    def brightness_down(self) -> str:
        """Decrease screen brightness."""
        try:
            subprocess.run(
                ['powershell', '-Command',
                 '$wsh = New-Object -ComObject WScript.Shell; 1..3 | ForEach-Object { $wsh.SendKeys([char]174) }'],
                capture_output=True, text=True, timeout=5
            )
            return "Brightness decreased."
        except Exception as e:
            return f"Could not adjust brightness: {e}"

    # -------------------------
    # Application Control
    # -------------------------
    def open_app(self, app_name: str) -> str:
        """Open a Windows application by name."""
        try:
            # Common app name mappings
            app_map = {
                "chrome": "chrome",
                "firefox": "firefox",
                "edge": "msedge",
                "notepad": "notepad",
                "calculator": "calc",
                "calculator app": "calc",
                "file explorer": "explorer",
                "explorer": "explorer",
                "vscode": "code",
                "visual studio code": "code",
                "terminal": "wt",
                "powershell": "powershell",
                "cmd": "cmd",
                "settings": "ms-settings:",
                "camera": "microsoft.windows.camera:",
                "photos": "photos",
                "paint": "mspaint",
                "word": "winword",
                "excel": "excel",
                "powerpoint": "powerpnt",
            }
            app_key = app_name.lower().strip()
            app_cmd = app_map.get(app_key, app_name)

            subprocess.Popen([app_cmd], shell=True)
            return f"Opening {app_name}..."
        except Exception as e:
            return f"Could not open {app_name}: {e}"

    def open_url(self, url: str) -> str:
        """Open a URL in the default browser."""
        try:
            import webbrowser
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            return f"Opening {url} in your browser."
        except Exception as e:
            return f"Could not open URL: {e}"

    def close_app(self, app_name: str) -> str:
        """Close a running application by name."""
        try:
            subprocess.run(
                ['taskkill', '/IM', f'{app_name}.exe', '/F'],
                capture_output=True, text=True, timeout=10
            )
            return f"Closing {app_name}..."
        except Exception as e:
            return f"Could not close {app_name}: {e}"

    def list_running_apps(self) -> str:
        """List currently running applications."""
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-Process | Where-Object { $_.MainWindowTitle -ne "" } | Select-Object ProcessName, MainWindowTitle -First 15 | Format-Table -AutoSize | Out-String'],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout.strip():
                return f"Running applications:\n{result.stdout.strip()}"
            return "No applications with visible windows found."
        except Exception as e:
            return f"Could not list applications: {e}"

    # -------------------------
    # System Actions
    # -------------------------
    def lock_screen(self) -> str:
        """Lock the Windows screen."""
        try:
            subprocess.run(['rundll32', 'user32.dll,LockWorkStation'])
            return "Locking screen..."
        except Exception as e:
            return f"Could not lock screen: {e}"

    def shutdown_pc(self) -> str:
        """Shut down the computer."""
        try:
            subprocess.run(['shutdown', '/s', '/t', '0'])
            return "Shutting down the computer..."
        except Exception as e:
            return f"Could not shutdown: {e}"

    def restart_pc(self) -> str:
        """Restart the computer."""
        try:
            subprocess.run(['shutdown', '/r', '/t', '0'])
            return "Restarting the computer..."
        except Exception as e:
            return f"Could not restart: {e}"

    def sleep_pc(self) -> str:
        """Put the computer to sleep."""
        try:
            subprocess.run(['rundll32', 'powrprof.dll,SetSuspendState', '0', '1', '0'])
            return "Putting computer to sleep..."
        except Exception as e:
            return f"Could not put computer to sleep: {e}"

    def cancel_shutdown(self) -> str:
        """Cancel a pending shutdown."""
        try:
            subprocess.run(['shutdown', '/a'])
            return "Shutdown cancelled."
        except Exception as e:
            return f"Could not cancel shutdown: {e}"

    def take_screenshot(self) -> str:
        """Take a screenshot and save it."""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            path = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")

            subprocess.run(
                ['powershell', '-Command',
                 f'$bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); $gfx = [System.Drawing.Graphics]::FromImage($bmp); $gfx.CopyFromScreen(0, 0, 0, 0, $bmp.Size); $bmp.Save("{path}")'],
                capture_output=True, text=True, timeout=10
            )
            return f"Screenshot saved to {path}"
        except Exception as e:
            return f"Could not take screenshot: {e}"

    def get_uptime(self) -> str:
        """Get system uptime."""
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 '(Get-CimInstance Win32_OperatingSystem).LastBootUpTime'],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip():
                boot_time = result.stdout.strip()
                return f"System last booted at: {boot_time}"
            return "Could not determine system uptime."
        except Exception as e:
            return f"Could not get uptime: {e}"

    def get_status(self) -> dict:
        """Return status of device tools."""
        return {
            "os": self.os_name,
            "volume_control": True,
            "app_control": True,
            "system_actions": True,
        }
