# Agent tools manager - orchestrates all tool categories
import os
import re
from typing import Optional


class AgentTools:
    """Central manager for all Haven agent tools.
    
    Parses user intent and routes to the appropriate tool.
    """

    def __init__(self):
        from .clock import ClockTools
        from .device import DeviceTools
        from .filesystem import FileSystemTools
        from .network import NetworkTools
        from .weather import WeatherTools
        from .youtube import YouTubeTools
        
        self.clock = ClockTools()
        self.device = DeviceTools()
        self.filesystem = FileSystemTools()
        self.network = NetworkTools()
        self.weather = WeatherTools()
        self.youtube = YouTubeTools()

    def get_tools_description(self) -> str:
        """Return a description of all available tools for the AI prompt."""
        return (
            "You have access to the following tools. When the user asks you to do something, "
            "respond with a tool call in this format: [[TOOL:tool_name:location:value]]\n"
            "Use the real parameter names from the list below, for example location, city, time, or minutes. "
            "Do NOT use a generic name like param or param1.\n\n"
            "Available tools:\n"
            "  time — Get current time\n"
            "  date — Get current date\n"
            "  datetime — Get current date and time\n"
            "  alarm — Set an alarm (format: HH:MM, message)\n"
            "  cancel_alarm — Cancel an alarm at HH:MM\n"
            "  list_alarms — List all alarms\n"
            "  timer — Set a timer (minutes, message)\n"
            "  cancel_timer — Cancel all timers\n"
            "  reminder — Set a reminder (minutes, message)\n"
            "  volume_up — Increase volume\n"
            "  volume_down — Decrease volume\n"
            "  mute — Toggle mute\n"
            "  brightness_up — Increase brightness\n"
            "  brightness_down — Decrease brightness\n"
            "  open — Open an app or URL\n"
            "  close_app — Close an application\n"
            "  running_apps — List running applications\n"
            "  screenshot — Take a screenshot\n"
            "  lock — Lock the screen\n"
            "  shutdown — Shut down the PC\n"
            "  restart — Restart the PC\n"
            "  sleep — Put PC to sleep\n"
            "  search_files — Search for files by name\n"
            "  open_file — Open a file\n"
            "  open_folder — Open a folder\n"
            "  folder_contents — List folder contents\n"
            "  file_info — Get file information\n"
            "  disk_usage — Get disk usage\n"
            "  ping — Ping a host\n"
            "  network_info — Get network interface info\n"
            "  network_stats — Get network traffic stats\n"
            "  wifi_info — Get WiFi information\n"
            "  scan_network — Scan local network for devices\n"
            "  internet_speed — Test internet speed\n"
            "  internet — Check internet connection\n"
            "  weather — Get weather for a location. Use this exact format: [[TOOL:weather:location:Castile]]\n"
            "  youtube_channel — Get channel info and recent videos\n"
            "  youtube_recent — Get recent videos from a channel\n"
            "  youtube_suggest — Suggest video titles based on channel content\n"
            "  youtube_set_channel — Set your default YouTube channel\n"
            "\nIf the user's request doesn't match any tool, just respond normally.\n"
            "For dangerous actions (shutdown, restart, lock), ask for confirmation first.\n"
        )

    def should_use_tool(self, message: str) -> bool:
        """Check if a message likely requires a tool."""
        tool_keywords = [
            "time", "date", "alarm", "timer", "reminder",
            "volume", "brightness", "mute",
            "open", "close", "launch", "start", "run",
            "screenshot", "lock", "shutdown", "restart", "sleep",
            "search", "find", "file", "folder", "disk",
            "ping", "network", "wifi", "internet", "speed",
            "weather", "temperature",
            "youtube",
        ]
        msg = message.lower()
        return any(kw in msg for kw in tool_keywords)

    def parse_and_execute(self, message: str) -> Optional[str]:
        """Parse a tool call from the AI's response and execute it.
        
        Returns the tool result string, or None if no tool call found.
        """
        # Look for [[TOOL:name:param:value...]] pattern
        pattern = r'\[\[TOOL:([a-z_]+)(:[^\]]*)?\]\]'
        match = re.search(pattern, message)
        
        if not match:
            return None

        tool_name = match.group(1)
        params_str = match.group(2)
        
        # Parse parameters
        # Haven Agent v1 fix: the model often writes param / param1 instead
        # of the real name, e.g. [[TOOL:weather:param:Castile,NY]].
        # Treat param / param1 as the first real parameter for that tool.
        params = {}
        if params_str:
            parts = params_str.strip(":").split(":")
            for i in range(0, len(parts) - 1, 2):
                key = parts[i]
                value = parts[i + 1] if i + 1 < len(parts) else ""
                if key in ("param", "param1", "value"):
                    # Map to the tool's main parameter
                    if tool_name == "weather":
                        key = "location"
                    elif tool_name in ("youtube_channel", "youtube_recent", "youtube_suggest"):
                        key = "channel"
                    elif tool_name in ("open", "close_app"):
                        key = "app"
                    elif tool_name in ("search_files",):
                        key = "query"
                    elif tool_name in ("open_file", "open_folder", "folder_contents", "file_info"):
                        key = "path"
                params[key] = value

        # Also try to extract key info directly from the message
        return self._execute_tool(tool_name, params, message)

    def _execute_tool(self, tool_name: str, params: dict, original_message: str) -> Optional[str]:
        """Execute a specific tool by name."""
        msg = original_message.lower()

        # ---- Clock tools ----
        if tool_name == "time":
            return self.clock.get_current_time()
        elif tool_name == "date":
            return self.clock.get_current_date()
        elif tool_name == "datetime":
            return self.clock.get_datetime()
        elif tool_name == "alarm":
            time_str = params.get("time", "")
            message = params.get("message", "Alarm!")
            if not time_str:
                # Try to extract time from message
                time_match = re.search(r'(\d{1,2}:\d{2})', original_message)
                if time_match:
                    time_str = time_match.group(1)
            if time_str:
                return self.clock.set_alarm(time_str, message)
            return "What time would you like the alarm for? (e.g., 7:30 AM or 07:30)"
        elif tool_name == "cancel_alarm":
            time_str = params.get("time", "")
            if not time_str:
                time_match = re.search(r'(\d{1,2}:\d{2})', original_message)
                if time_match:
                    time_str = time_match.group(1)
            return self.clock.cancel_alarm(time_str) if time_str else self.clock.list_alarms()
        elif tool_name == "list_alarms":
            return self.clock.list_alarms()
        elif tool_name == "timer":
            minutes = params.get("minutes", params.get("time", ""))
            message = params.get("message", "Timer done!")
            if not minutes:
                num_match = re.search(r'(\d+)', original_message)
                if num_match:
                    minutes = num_match.group(1)
            if minutes:
                return self.clock.set_timer(float(minutes), message)
            return "How many minutes for the timer?"
        elif tool_name == "cancel_timer":
            return self.clock.cancel_timer()
        elif tool_name == "reminder":
            minutes = params.get("minutes", params.get("time", ""))
            message = params.get("message", "")
            if not minutes:
                num_match = re.search(r'(\d+)', original_message)
                if num_match:
                    minutes = num_match.group(1)
            if minutes and message:
                return self.clock.set_reminder(float(minutes), message)
            return "How many minutes and what should I remind you about?"

        # ---- Device tools ----
        elif tool_name == "volume_up":
            return self.device.volume_up()
        elif tool_name == "volume_down":
            return self.device.volume_down()
        elif tool_name == "mute":
            return self.device.mute_volume()
        elif tool_name == "brightness_up":
            return self.device.brightness_up()
        elif tool_name == "brightness_down":
            return self.device.brightness_down()
        elif tool_name == "open":
            target = params.get("app", params.get("url", params.get("name", "")))
            if not target:
                # Extract from message
                for word in ["open", "launch", "start", "run"]:
                    idx = msg.find(word)
                    if idx >= 0:
                        target = original_message[idx + len(word):].strip()
                        break
            if target:
                if target.startswith(("http://", "https://", "www.")):
                    return self.device.open_url(target)
                return self.device.open_app(target)
            return "What would you like me to open?"
        elif tool_name == "close_app":
            app = params.get("app", params.get("name", ""))
            if not app:
                return "Which application would you like me to close?"
            return self.device.close_app(app)
        elif tool_name == "running_apps":
            return self.device.list_running_apps()
        elif tool_name == "screenshot":
            return self.device.take_screenshot()
        elif tool_name == "lock":
            return self.device.lock_screen()
        elif tool_name == "shutdown":
            return self.device.shutdown_pc()
        elif tool_name == "restart":
            return self.device.restart_pc()
        elif tool_name == "sleep":
            return self.device.sleep_pc()

        # ---- File system tools ----
        elif tool_name == "search_files":
            query = params.get("query", params.get("name", ""))
            if not query:
                return "What files would you like me to search for?"
            return self.filesystem.search_files(query)
        elif tool_name == "open_file":
            path = params.get("path", params.get("file", ""))
            if not path:
                return "Which file would you like me to open?"
            return self.filesystem.open_file(path)
        elif tool_name == "open_folder":
            path = params.get("path", params.get("folder", ""))
            if not path:
                return "Which folder would you like me to open?"
            return self.filesystem.open_folder(path)
        elif tool_name == "folder_contents":
            path = params.get("path", params.get("folder", ""))
            if not path:
                path = os.path.expanduser("~")
            return self.filesystem.get_folder_contents(path)
        elif tool_name == "file_info":
            path = params.get("path", params.get("file", ""))
            if not path:
                return "Which file would you like information about?"
            return self.filesystem.get_file_info(path)
        elif tool_name == "disk_usage":
            return self.filesystem.get_disk_usage()

        # ---- Network tools ----
        elif tool_name == "ping":
            host = params.get("host", params.get("ip", ""))
            if not host:
                return "Which host would you like me to ping?"
            return self.network.ping_host(host)
        elif tool_name == "network_info":
            return self.network.get_network_info()
        elif tool_name == "network_stats":
            return self.network.get_network_stats()
        elif tool_name == "wifi_info":
            return self.network.get_wifi_info()
        elif tool_name == "scan_network":
            return self.network.scan_local_network()
        elif tool_name == "internet_speed":
            return self.network.get_internet_speed()
        elif tool_name == "internet":
            return self.network.check_internet()

        # ---- Weather tools ----
        # Haven Agent v1 fix: the old code looked in Haven's OWN reply and
        # took the last word after in/for/at, so "for your area!" became
        # location "area!" and weather always said "Location not found".
        # Now: use the location from the tool call first. If there is none,
        # get_weather() will use the default city, Castile, NY.
        # We do NOT guess a location from the reply text any more.
        elif tool_name == "weather":
            location = params.get("location", params.get("city", params.get("param", "")))
            if location:
                location = location.strip().strip(",.!")
                if location.lower() in ("area", "area!", "the area"):
                    location = ""
            return self.weather.get_weather(location if location else None)

        # ---- YouTube tools ----
        elif tool_name == "youtube_channel":
            channel = params.get("channel", params.get("id", params.get("name", "")))
            if not channel:
                # Try to extract channel from message - handles URLs, handles, and IDs
                channel_match = re.search(r'(youtube\.com/@[\w\d]+|@[\w\d]+|UC[\w\-_]+)', original_message)
                if channel_match:
                    channel = channel_match.group(1)
            return self.youtube.get_channel_info(channel)
        elif tool_name == "youtube_recent":
            channel = params.get("channel", params.get("id", params.get("name", "")))
            count = params.get("count", "10")
            if not channel:
                channel_match = re.search(r'(youtube\.com/@[\w\d]+|@[\w\d]+|UC[\w\-_]+)', original_message)
                if channel_match:
                    channel = channel_match.group(1)
            try:
                count = int(count)
            except ValueError:
                count = 10
            return self.youtube.get_recent_videos(channel, count)
        elif tool_name == "youtube_suggest":
            channel = params.get("channel", params.get("id", params.get("name", "")))
            if not channel:
                channel_match = re.search(r'(youtube\.com/@[\w\d]+|@[\w\d]+|UC[\w\-_]+)', original_message)
                if channel_match:
                    channel = channel_match.group(1)
            return self.youtube.suggest_video_titles(channel)
        elif tool_name == "youtube_set_channel":
            channel = params.get("channel", params.get("id", params.get("name", "")))
            if not channel:
                # Extract channel from message - handles full URLs, handles, and IDs
                channel_match = re.search(r'(youtube\.com/[\w\./@]+|@[\w\d]+|UC[\w\-_]+)', original_message)
                if channel_match:
                    channel = channel_match.group(1)
            if channel:
                return self.youtube.set_channel(channel)
            return "Please provide a channel ID (UC...), handle (@name), or YouTube URL."

        return None

    def get_status(self) -> dict:
        """Return status of all tool categories."""
        return {
            "clock": self.clock.get_status(),
            "device": self.device.get_status(),
            "filesystem": self.filesystem.get_status(),
            "network": self.network.get_status(),
            "weather": self.weather.get_status(),
            "youtube": self.youtube.get_status(),
        }
