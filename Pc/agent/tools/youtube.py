# YouTube tools - scan and analyze YouTube channel
import urllib.request
import json
import re
import os
from datetime import datetime


class YouTubeTools:
    """YouTube channel analysis tools for Haven.
    
    Uses the YouTube Data API v3 to scan channels, videos, and stats.
    No API key required for public channel info via RSS/Atom feeds.
    """

    def __init__(self):
        self.api_key = None  # Optional YouTube Data API key for advanced features
        self.default_channel = None
        # Persist channel config to file so it survives across API calls
        self._config_path = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "youtube_config.json")
        self._load_config()

    def _load_config(self):
        """Load saved YouTube config from file."""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, "r") as f:
                    config = json.load(f)
                self.default_channel = config.get("default_channel")
                self.api_key = config.get("api_key")
        except Exception:
            pass

    def _save_config(self):
        """Save YouTube config to file."""
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            config = {
                "default_channel": self.default_channel,
                "api_key": self.api_key
            }
            with open(self._config_path, "w") as f:
                json.dump(config, f)
        except Exception:
            pass

    def set_api_key(self, api_key: str) -> str:
        """Set YouTube Data API key for advanced features."""
        self.api_key = api_key
        return "YouTube API key set. Advanced features are now available."

    def set_channel(self, channel_identifier: str) -> str:
        """Set the default channel to analyze.
        
        Accepts channel ID (UC...), channel handle (@...), or channel URL.
        """
        # Extract channel ID or handle from URL
        if "youtube.com" in channel_identifier:
            # Try to extract handle from URL like youtube.com/@name
            match = re.search(r'@([\w\d]+)', channel_identifier)
            if match:
                channel_identifier = f"@{match.group(1)}"
            else:
                # Try to extract channel ID
                match = re.search(r'channel/([\w\d\-_]+)', channel_identifier)
                if match:
                    channel_identifier = match.group(1)
        
        self.default_channel = channel_identifier
        self._save_config()  # Persist to file
        return f"Default channel set to: {channel_identifier}"

    def get_channel_info(self, channel_identifier: str = None) -> str:
        """Get basic channel info from the channel's about page (no API key needed).
        
        Uses RSS feed to get recent videos and basic info.
        """
        channel = channel_identifier or self.default_channel
        if not channel:
            return "No channel set. Please provide a channel ID, handle (@name), or URL."

        try:
            # Build the RSS feed URL
            if channel.startswith("@"):
                # Handle format
                feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self._resolve_handle(channel)}"
            elif channel.startswith("UC"):
                # Channel ID format
                feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
            else:
                return f"Please provide a valid channel ID (UC...) or handle (@name). Got: {channel}"

            if not feed_url.startswith("https://www.youtube.com/feeds"):
                return feed_url  # Error message from resolve

            # Fetch the RSS feed
            req = urllib.request.Request(
                feed_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                feed_data = resp.read().decode("utf-8")

            # Parse the XML feed for basic info
            channel_name_match = re.search(r'<name>(.*?)</name>', feed_data)
            channel_name = channel_name_match.group(1) if channel_name_match else "Unknown"

            # Extract recent videos
            videos = []
            video_pattern = re.compile(
                r'<entry>.*?<yt:videoId>(.*?)</yt:videoId>.*?<title>(.*?)</title>.*?<link rel="alternate" href="(.*?)".*?<published>(.*?)</published>',
                re.DOTALL
            )
            
            for match in video_pattern.finditer(feed_data):
                video_id = match.group(1).strip()
                title = match.group(2).strip()
                url = match.group(3)
                published = match.group(4).strip()
                videos.append({
                    "title": title,
                    "url": url,
                    "published": published[:10],  # Just the date part
                    "video_id": video_id
                })

            if not videos:
                return f"Channel: {channel_name}\nNo recent videos found in the feed."

            # Format the response
            result = f"Channel: {channel_name}\n"
            result += f"Recent videos (up to 15):\n\n"
            
            for i, video in enumerate(videos[:15], 1):
                result += f"{i}. {video['title']}\n"
                result += f"   Published: {video['published']}\n"
                result += f"   URL: {video['url']}\n\n"

            return result

        except urllib.error.URLError as e:
            return f"Could not reach YouTube. Please check your internet connection. Error: {e}"
        except Exception as e:
            return f"Failed to get channel info: {e}"

    def get_recent_videos(self, channel_identifier: str = None, count: int = 10) -> str:
        """Get recent videos from a channel's RSS feed."""
        channel = channel_identifier or self.default_channel
        if not channel:
            return "No channel set. Please provide a channel ID, handle (@name), or URL."

        try:
            # Build the RSS feed URL
            if channel.startswith("@"):
                resolved = self._resolve_handle(channel)
                if not resolved.startswith("UC"):
                    return resolved  # Error message
                feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={resolved}"
            elif channel.startswith("UC"):
                feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
            else:
                return "Please provide a valid channel ID (UC...) or handle (@name)."

            # Fetch the RSS feed
            req = urllib.request.Request(
                feed_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                feed_data = resp.read().decode("utf-8")

            # Extract videos
            videos = []
            video_pattern = re.compile(
                r'<entry>.*?<yt:videoId>(.*?)</yt:videoId>.*?<title>(.*?)</title>.*?<link rel="alternate" href="(.*?)".*?<published>(.*?)</published>',
                re.DOTALL
            )

            for match in video_pattern.finditer(feed_data):
                video_id = match.group(1).strip()
                title = match.group(2).strip()
                url = match.group(3)
                published = match.group(4).strip()[:10]
                videos.append({
                    "title": title,
                    "url": url,
                    "published": published,
                    "video_id": video_id
                })

            if not videos:
                return "No videos found in the feed."

            # Format the response
            result = f"Recent videos from channel (showing {min(count, len(videos))}):\n\n"
            
            for i, video in enumerate(videos[:count], 1):
                result += f"{i}. {video['title']}\n"
                result += f"   Published: {video['published']}\n"
                result += f"   Watch: https://youtube.com/watch?v={video['video_id']}\n\n"

            return result

        except urllib.error.URLError as e:
            return f"Could not reach YouTube. Error: {e}"
        except Exception as e:
            return f"Failed to get recent videos: {e}"

    def get_video_stats(self, video_id: str) -> str:
        """Get stats for a specific video using the YouTube API (requires API key)."""
        if not self.api_key:
            return "This feature requires a YouTube Data API key. You can get one from Google Cloud Console."

        try:
            url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id={video_id}&key={self.api_key}"
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            if not data.get("items"):
                return f"Video not found: {video_id}"

            video = data["items"][0]
            stats = video.get("statistics", {})
            snippet = video.get("snippet", {})

            result = f"Video: {snippet.get('title', 'Unknown')}\n"
            result += f"Published: {snippet.get('publishedAt', 'Unknown')[:10]}\n\n"
            result += f"Views: {stats.get('viewCount', 'N/A')}\n"
            result += f"Likes: {stats.get('likeCount', 'N/A')}\n"
            result += f"Comments: {stats.get('commentCount', 'N/A')}\n"
            result += f"Favorites: {stats.get('favoriteCount', '0')}\n"

            return result

        except urllib.error.URLError as e:
            return f"Could not reach YouTube API. Error: {e}"
        except Exception as e:
            return f"Failed to get video stats: {e}"

    def get_channel_stats(self, channel_identifier: str = None) -> str:
        """Get channel statistics using the YouTube API (requires API key)."""
        if not self.api_key:
            return "This feature requires a YouTube Data API key. You can get one from Google Cloud Console."

        channel = channel_identifier or self.default_channel
        if not channel:
            return "No channel set."

        try:
            # Search for the channel
            search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={channel}&type=channel&key={self.api_key}"
            with urllib.request.urlopen(search_url, timeout=15) as resp:
                search_data = json.loads(resp.read().decode())

            if not search_data.get("items"):
                return f"Channel not found: {channel}"

            channel_id = search_data["items"][0]["id"]["channelId"]

            # Get channel stats
            stats_url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics,snippet&id={channel_id}&key={self.api_key}"
            with urllib.request.urlopen(stats_url, timeout=15) as resp:
                stats_data = json.loads(resp.read().decode())

            channel_info = stats_data["items"][0]
            stats = channel_info.get("statistics", {})
            snippet = channel_info.get("snippet", {})

            result = f"Channel: {snippet.get('title', 'Unknown')}\n"
            result += f"Description: {snippet.get('description', 'N/A')[:100]}...\n\n"
            result += f"Subscribers: {stats.get('subscriberCount', 'N/A')}\n"
            result += f"Total Views: {stats.get('viewCount', 'N/A')}\n"
            result += f"Total Videos: {stats.get('videoCount', 'N/A')}\n"

            return result

        except urllib.error.URLError as e:
            return f"Could not reach YouTube API. Error: {e}"
        except Exception as e:
            return f"Failed to get channel stats: {e}"

    def suggest_video_titles(self, channel_identifier: str = None, count: int = 5) -> str:
        """Suggest video titles based on recent channel content (no API key needed)."""
        channel = channel_identifier or self.default_channel
        if not channel:
            return "No channel set."

        # Get recent videos first
        recent_result = self.get_recent_videos(channel, count=10)
        
        if "Failed" in recent_result or "Could not" in recent_result:
            return recent_result

        # Extract titles from the result
        titles = re.findall(r'^\d+\\. (.+)$', recent_result, re.MULTILINE)
        
        if not titles:
            return "Could not analyze recent videos for suggestions."

        # Generate suggestions based on patterns
        suggestions = []
        
        # Pattern 1: "Part 2" or continuation style
        for title in titles[:3]:
            if "Part" not in title and "Ep." not in title:
                suggestions.append(f"{title} - Part 2")

        # Pattern 2: "Best of" compilation
        if len(titles) >= 3:
            suggestions.append(f"Best of {channel} - Top Moments Compilation")

        # Pattern 3: "How to" guide based on content
        suggestions.append("Behind the Scenes: How I Create My Content")

        # Pattern 4: Q&A style
        suggestions.append("Answering Your Questions - Q&A Session")

        # Pattern 5: Collaboration idea
        suggestions.append("Collaboration Challenge - You Suggest, I Create")

        # Remove duplicates and limit
        suggestions = list(dict.fromkeys(suggestions))[:count]

        result = "Video Title Suggestions based on your recent content:\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            result += f"{i}. {suggestion}\n"

        return result

    def _resolve_handle(self, handle: str) -> str:
        """Resolve a channel handle (@name) to a channel ID.
        
        This is a best-effort approach using the RSS feed.
        Returns the channel ID or an error message.
        """
        try:
            # Try to fetch the channel page to find the channel ID
            url = f"https://www.youtube.com/{handle}/about"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                page_content = resp.read().decode("utf-8")

            # Look for channel ID in the page source
            match = re.search(r'channel_id["\s:]+(UC[\w\-_]+)', page_content)
            if match:
                return match.group(1)

            # Alternative pattern
            match = re.search(r'externalChannelId["\s:]+["\']?(UC[\w\-_]++)', page_content)
            if match:
                return match.group(1)

            return "Could not resolve handle to channel ID. Please provide the channel ID directly."

        except Exception as e:
            return f"Failed to resolve handle: {e}"

    def get_status(self) -> dict:
        """Return status of YouTube tools."""
        return {
            "default_channel": self.default_channel,
            "api_key_set": self.api_key is not None,
            "features": "RSS feed (no API key) + YouTube Data API (with key)",
        }
