"""
Restaurant Tool
===============
Fetches nearby restaurants using Nominatim + Overpass API.
"""

import requests


def restaurant_tool(location: str, near_location: str = None) -> dict:
    """Get nearby restaurants for a location.
    
    Args:
        location: Main destination city
        near_location: Optional specific place/attraction to search restaurants near. If provided, restaurants are searched near this location instead of the city center.
    """

    headers = {
        "User-Agent": "smart-travel-mcp-agent"
    }

    try:
        # ------- Step 1: Geocode -------
        # Use near_location if provided, otherwise use main location
        search_location = near_location if near_location else location
        
        geo_url = "https://nominatim.openstreetmap.org/search"
        geo_params = {"q": search_location, "format": "json"}

        geo_res = requests.get(geo_url, headers=headers, params=geo_params, timeout=10)
        geo_data = geo_res.json()

        if not geo_data:
            return {"error": f"Location '{search_location}' not found"}

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]

        # ------- Step 2: Overpass API for restaurants -------
        query = f"""
        [out:json];
        node
          ["amenity"="restaurant"]
          (around:3000,{lat},{lon});
        out;
        """

        overpass_headers = {
            "User-Agent": "smart-travel-mcp-agent",
            "Accept": "application/json",
            "Content-Type": "text/plain; charset=utf-8"
        }

        res = requests.post(
            "https://overpass-api.de/api/interpreter",
            headers=overpass_headers,
            data=query.encode("utf-8"),
            timeout=15
        )

        if res.status_code != 200:
            return {"error": f"Overpass API returned status {res.status_code}"}

        data = res.json()

        restaurants = []
        for place in data.get("elements", [])[:8]:
            name = place.get("tags", {}).get("name")
            if name:
                cuisine = place.get("tags", {}).get("cuisine", "local")
                restaurants.append({
                    "name": name,
                    "cuisine": cuisine
                })

        if not restaurants:
            return {"error": "No restaurants found from API"}

        return {
            "location": location,
            "restaurants": restaurants
        }

    except requests.exceptions.Timeout:
        return {"error": "Restaurant API timed out"}
    except Exception as e:
        return {"error": str(e)}