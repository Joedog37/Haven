# Network tools - discovery, speed test, ping
import subprocess
import platform
import json


class NetworkTools:
    """Network discovery and monitoring tools for Haven."""

    def __init__(self):
        self.os_name = platform.system()

    def check_internet(self) -> str:
        """Check if internet connection is available."""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '8.8.8.8'] if self.os_name != 'Windows'
                else ['ping', '-n', '1', '8.8.8.8'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return "Internet connection is active."
            else:
                return "No internet connection detected."
        except subprocess.TimeoutExpired:
            return "Ping timed out — internet connection may be down."
        except Exception as e:
            return f"Could not check internet: {e}"

    def ping_host(self, host: str) -> str:
        """Ping a host and return the result."""
        try:
            cmd = ['ping', '-n', '4', host] if self.os_name == 'Windows' else ['ping', '-c', '4', host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Could not reach {host}."
        except subprocess.TimeoutExpired:
            return f"Ping to {host} timed out."
        except Exception as e:
            return f"Ping failed: {e}"

    def get_network_info(self) -> str:
        """Get current network interface information."""
        try:
            import psutil
            addrs = psutil.net_if_addrs()
            info = []
            for name, sniclist in addrs.items():
                for snic in sniclist:
                    if snic.family == 'AF_INET' and snic.address and not snic.address.startswith('127.'):
                        info.append(f"  {name}: {snic.address}")

            if info:
                return "Network interfaces:\n" + "\n".join(info)
            return "No network interfaces found."
        except Exception as e:
            return f"Could not get network info: {e}"

    def get_network_stats(self) -> str:
        """Get network traffic statistics."""
        try:
            import psutil
            counters = psutil.net_io_counters()
            bytes_sent = counters.bytes_sent
            bytes_recv = counters.bytes_recv

            def format_bytes(b):
                if b > 1024**3:
                    return f"{b / (1024**3):.1f} GB"
                elif b > 1024**2:
                    return f"{b / (1024**2):.1f} MB"
                elif b > 1024:
                    return f"{b / 1024:.1f} KB"
                return f"{b} bytes"

            return (f"Network statistics:\n"
                    f"  Sent: {format_bytes(bytes_sent)}\n"
                    f"  Received: {format_bytes(bytes_recv)}\n"
                    f"  Packets sent: {counters.packets_sent}\n"
                    f"  Packets received: {counters.packets_recv}")
        except Exception as e:
            return f"Could not get network stats: {e}"

    def get_wifi_info(self) -> str:
        """Get WiFi connection information (Windows)."""
        try:
            if self.os_name != 'Windows':
                return "WiFi info is only available on Windows."

            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "No WiFi interface found."
        except Exception as e:
            return f"Could not get WiFi info: {e}"

    def scan_local_network(self) -> str:
        """Scan the local network for active devices."""
        try:
            # Get local IP to determine subnet
            import psutil
            addrs = psutil.net_if_addrs()
            local_ip = None
            for name, sniclist in addrs.items():
                for snic in sniclist:
                    if snic.family == 'AF_INET' and snic.address and not snic.address.startswith('127.'):
                        local_ip = snic.address
                        break
                if local_ip:
                    break

            if not local_ip:
                return "Could not determine local IP address."

            subnet = '.'.join(local_ip.split('.')[:3])
            devices = []

            # Quick ping scan of common IPs
            for i in range(1, 255):
                ip = f"{subnet}.{i}"
                try:
                    cmd = ['ping', '-n', '1', '-w', '500', ip] if self.os_name == 'Windows' else ['ping', '-c', '1', '-W', '0.5', ip]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        devices.append(ip)
                except subprocess.TimeoutExpired:
                    continue

            if devices:
                lines = [f"Found {len(devices)} active device(s) on {subnet}.0/24:"]
                lines.extend(f"  {ip}" for ip in devices)
                return "\n".join(lines)
            else:
                return f"No other active devices found on {subnet}.0/24."
        except Exception as e:
            return f"Network scan failed: {e}"

    def get_internet_speed(self) -> str:
        """Estimate internet speed using a simple download test."""
        try:
            import urllib.request
            import time

            # Test with a small file from a CDN
            url = "https://speed.cloudflare.com/__down?bytes=1000000"  # 1MB test
            start = time.time()
            urllib.request.urlopen(url, timeout=10)
            elapsed = time.time() - start

            if elapsed > 0:
                speed_mbps = (1_000_000 / elapsed) / (1024 * 1024) * 8
                return f"Estimated download speed: {speed_mbps:.1f} Mbps"
            return "Could not measure speed."
        except Exception as e:
            return f"Speed test failed: {e}"

    def get_status(self) -> dict:
        """Return status of network tools."""
        return {
            "os": self.os_name,
            "ping": True,
            "scan": True,
            "wifi": self.os_name == 'Windows',
        }
