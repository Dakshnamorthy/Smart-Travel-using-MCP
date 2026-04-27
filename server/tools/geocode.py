"""
Geocode Tool
============
Converts a location name into latitude/longitude coordinates.
Uses Nominatim (OpenStreetMap) — free, no API key needed.
"""

import requests


def geocode_tool(location: str) -> dict:
    """Convert location name into lat/lon coordinates."""

    url = "https://nominatim.openstreetmap.org/search"

    headers = {
        "User-Agent": "smart-travel-mcp-agent"
    }

    params = {
        "q": location,
        "format": "json"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code != 200:
            return {"error": f"Geocode API returned status {response.status_code}"}

        data = response.json()

        if not data:
            return {"error": f"Location '{location}' not found"}

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])

        return {
            "location": location,
            "latitude": lat,
            "longitude": lon,
            # Short aliases for convenience (used by distance_tool)
            "lat": lat,
            "lon": lon
        }

    except Exception as e:
        return {"error": str(e)}