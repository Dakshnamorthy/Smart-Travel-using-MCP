"""
Distance Tool
=============
Calculates distance between two locations using:
  1. ORS (OpenRouteService) API — primary
  2. Haversine formula — fallback

Depends on: geocode_tool
"""

import requests
import os
import math
from dotenv import load_dotenv
from server.tools.geocode import geocode_tool

load_dotenv()

API_KEY = os.getenv("ORS_API_KEY")


def haversine(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance between two points (km)."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def distance_tool(origin: str, destination: str) -> dict:
    """Calculate distance and travel time between two locations."""
    try:
        # ------- Step 1: Geocode both locations -------
        src_data = geocode_tool(origin)
        dest_data = geocode_tool(destination)

        # Check for geocode errors
        if "error" in src_data:
            return {"error": f"Could not geocode origin '{origin}': {src_data['error']}"}
        if "error" in dest_data:
            return {"error": f"Could not geocode destination '{destination}': {dest_data['error']}"}

        # Use the short keys (now guaranteed by fixed geocode_tool)
        src_lat = float(src_data["lat"])
        src_lon = float(src_data["lon"])
        dest_lat = float(dest_data["lat"])
        dest_lon = float(dest_data["lon"])

        # ------- Step 2: Try ORS API -------
        if API_KEY:
            url = "https://api.openrouteservice.org/v2/directions/driving-car"

            headers = {
                "Authorization": API_KEY,
                "Content-Type": "application/json"
            }

            body = {
                "coordinates": [
                    [src_lon, src_lat],
                    [dest_lon, dest_lat]
                ]
            }

            response = requests.post(url, json=body, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                summary = data["routes"][0]["summary"]

                return {
                    "origin": origin,
                    "destination": destination,
                    "distance_km": round(summary["distance"] / 1000, 2),
                    "duration_hours": round(summary["duration"] / 3600, 2)
                }

        # ------- Step 3: Fallback to Haversine -------
        distance_km = haversine(src_lat, src_lon, dest_lat, dest_lon)

        return {
            "origin": origin,
            "destination": destination,
            "distance_km": round(distance_km, 2),
            "duration_hours": round(distance_km / 50, 2),  # rough estimate at 50 km/h
            "note": "Estimated using straight-line distance (fallback)"
        }

    except Exception as e:
        return {"error": str(e)}