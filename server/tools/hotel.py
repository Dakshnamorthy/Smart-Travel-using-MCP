"""
Hotel Tool
==========
Fetches nearby hotels using Nominatim + Overpass API.
"""

import requests


def hotel_tool(location: str, budget: str = "medium", near_location: str = None) -> dict:
    """Get hotel recommendations for a location.
    
    Args:
        location: Main destination city
        budget: Budget level (low, medium, high)
        near_location: Optional specific place/attraction to search hotels near. If provided, hotels are searched near this location instead of the city center.
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

        # ------- Step 2: Overpass API for hotels -------
        query = f"""
        [out:json];
        node
          ["tourism"="hotel"]
          (around:5000,{lat},{lon});
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

        hotels = []
        for place in data.get("elements", [])[:8]:
            name = place.get("tags", {}).get("name")
            if name:
                stars = place.get("tags", {}).get("stars", "N/A")
                hotels.append({
                    "name": name,
                    "price": "Varies",
                    "stars": stars
                })

        if not hotels:
            return {"error": "No hotels found from API"}

        return {
            "location": location,
            "budget": budget,
            "hotels": hotels
        }

    except requests.exceptions.Timeout:
        return {"error": "Hotel API timed out"}
    except Exception as e:
        return {"error": str(e)}