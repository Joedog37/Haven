# Weather tools - get weather information
import urllib.request
import json


class WeatherTools:
    """Weather information tools for Haven."""

    def __init__(self):
        self.default_city = "Castile, NY"  # Haven Agent v1: Joseph lives in Castile, NY 14427


    def _clean_location(self, location):
        """Haven Agent v1 fix: turn messy model text into a real place name.

        Examples: "Castile,NY,14427" -> "Castile"
                  "Castile, NY" -> "Castile"
                  "area!" / "area" / "" -> "" (so the default city is used)
                  "New York" -> "New York"
        Open-Meteo geocoding works best with just the town/city name.
        A zip code on its own is not a place name for this service.
        """
        if not location:
            return ""
        loc = str(location).strip().strip(",.!")
        # Drop anything in brackets - leftover tool text
        import re
        loc = re.sub(r"\[[^\]]*\]", "", loc).strip()
        loc = loc.strip(",.!")
        if not loc:
            return ""
        # If it is just a zip code, we cannot geocode it - use default city
        if re.fullmatch(r"\d{5}(-\d{4})?", loc):
            return ""
        # "Castile,NY,14427" / "Castile, NY" -> take the town name first
        first = loc.split(",")[0].strip()
        # Never accept "area" as a place - that was the old manager bug
        if first.lower() in ("area", "area!", "the area", "your area"):
            return ""
        return first

    def get_weather(self, location: str = None) -> str:
        """Get current weather for a location using Open-Meteo (free, no API key)."""
        try:
            city = self._clean_location(location) or self.default_city

            # Geocode the city to lat/lon using Open-Meteo geocoding API
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.request.quote(city)}&count=1&language=en&format=json"
            with urllib.request.urlopen(geo_url, timeout=10) as resp:
                geo_data = json.loads(resp.read().decode())

            if not geo_data.get("results"):
                return f"Location not found: {city}. Please try a different city name."

            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            place_name = result.get("name", city)
            country = result.get("country", "")

            # Get weather data
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
                f"&daily=temperature_2m_max,temperature_2m_min,weather_code"
                f"&temperature_unit=fahrenheit&wind_speed_unit=mph"
                f"&forecast_days=2"
            )
            with urllib.request.urlopen(weather_url, timeout=10) as resp:
                weather_data = json.loads(resp.read().decode())

            current = weather_data["current"]
            daily = weather_data["daily"]

            temp = current["temperature_2m"]
            humidity = current["relative_humidity_2m"]
            wind = current["wind_speed_10m"]
            code = current["weather_code"]
            condition = self._weather_code_to_text(code)

            high = daily["temperature_2m_max"][0]  # Haven Agent v1 fix: [0] is today, [1] was tomorrow
            low = daily["temperature_2m_min"][0]

            weather = (
                f"Weather in {place_name}, {country}:\n"
                f"  Current: {condition} at {temp}°F\n"
                f"  Humidity: {humidity}%\n"
                f"  Wind: {wind} mph\n"
                f"  Today's high: {high}°F / Low: {low}°F"
            )
            return weather
        except urllib.error.HTTPError as e:
            # Haven Agent v1 fix: say the real error, do not hide it.
            # 429 = Open-Meteo is rate-limiting us, try again in a minute.
            if e.code == 429:
                return "Weather service is busy right now (too many requests). Please try again in a minute."
            return f"Weather service returned an error ({e.code}). Please try again later."
        except urllib.error.URLError:
            return "Could not reach weather service. Please check your internet connection."
        except Exception as e:
            return f"Weather lookup failed: {e}"

    def set_default_city(self, city: str) -> str:
        """Set the default city for weather lookups."""
        self.default_city = city
        return f"Default weather city set to {city}."

    def _weather_code_to_text(self, code: int) -> str:
        """Convert WMO weather code to human-readable text."""
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snowfall",
            73: "Moderate snowfall",
            75: "Heavy snowfall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return codes.get(code, f"Unknown (code {code})")

    def get_status(self) -> dict:
        """Return status of weather tools."""
        return {
            "default_city": self.default_city,
            "service": "Open-Meteo (free, no API key)",
        }
