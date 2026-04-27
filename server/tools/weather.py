"""
Weather Tool
============
Gets current weather for a location using OpenWeatherMap API.
"""

import requests
import os


def weather_tool(location: str) -> dict:
    """Get current weather for a location."""

    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        return {"error": "OPENWEATHER_API_KEY not set in environment"}

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"

        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return {"error": f"Weather API returned status {response.status_code}"}

        data = response.json()

        # Validate that we got real data
        temp = data.get("main", {}).get("temp")
        if temp is None:
            return {"error": "Weather data incomplete"}

        return {
            "location": location,
            "temperature": temp,
            "description": data.get("weather", [{}])[0].get("description", "unknown"),
            "humidity": data.get("main", {}).get("humidity"),
            "wind_speed": data.get("wind", {}).get("speed")
        }

    except requests.exceptions.Timeout:
        return {"error": "Weather API timed out"}
    except Exception as e:
        return {"error": str(e)}