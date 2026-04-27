"""
Attraction Tool
===============
Fetches top tourist attractions for a location.
Uses Nominatim for geocoding + OpenTripMap for attraction data.
"""

import requests
import os


def attraction_tool(location: str, category_preference: str = None) -> dict:
    """Get top tourist attractions for a location."""

    headers = {
        "User-Agent": "smart-travel-mcp-agent"
    }

    try:
        # ------- Step 1: Geocode -------
        geo_url = "https://nominatim.openstreetmap.org/search"
        geo_params = {"q": location, "format": "json"}

        geo_res = requests.get(geo_url, headers=headers, params=geo_params, timeout=10)

        if geo_res.status_code != 200:
            return {"error": f"Geocode failed with status {geo_res.status_code}"}

        geo_data = geo_res.json()

        if not geo_data:
            return {"error": f"Location '{location}' not found"}

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]

        # ------- Step 2: Get attractions from OpenTripMap -------
        api_key = os.getenv("OPENTRIPMAP_API_KEY")

        if not api_key:
            return {"error": "OPENTRIPMAP_API_KEY not set"}

        url = "https://api.opentripmap.com/0.1/en/places/radius"

        # Determine kinds based on preference
        kinds = "interesting_places,architecture,cultural,historic,museums,natural,beaches,gardens_and_parks,monuments_and_memorials,fortifications,palaces,theatres_and_entertainments,view_points"
        if category_preference:
            pref = category_preference.lower()
            if "beach" in pref:
                kinds = "beaches"
            elif "water" in pref or "fall" in pref or "falls" in pref:
                kinds = "natural"
            elif "relig" in pref or "temple" in pref or "church" in pref:
                kinds = "religion"
            elif "histor" in pref or "fort" in pref:
                kinds = "historic,fortifications,palaces,monuments_and_memorials"
            elif "natur" in pref or "park" in pref:
                kinds = "natural,gardens_and_parks,view_points"

        # WHY these params:
        # - rate=3: Only places rated 3+ stars (filters out random minor sites)
        # - radius=50000: 50km to find enough quality places across a whole state
        # - limit=300: Fetch a massive radius net because OTM sorts by distance natively!
        #              If we limit too small, we only get the center coordinate (e.g., inland Goa churches)
        #              and never reach the beaches before capping out.
        params = {
            "radius": 50000,
            "lon": lon,
            "lat": lat,
            "format": "json",
            "limit": 300,
            "rate": "3",
            "kinds": kinds,
            "apikey": api_key
        }

        res = requests.get(url, params=params, timeout=10)

        if res.status_code != 200:
            return {"error": f"OpenTripMap returned status {res.status_code}"}

        data = res.json()
        
        # If no rate=3 places found (likely a smaller city like Thanjavur),
        # retry without the rate restriction to get at least something real
        if not data:
            del params["rate"]
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()

        # Sort by rate (highest rated first) then take top 10
        if isinstance(data, list):
            data.sort(key=lambda x: x.get("rate", 0), reverse=True)

        attractions = []
        seen_names = set()
        
        # Words we explicitly DO NOT want in our tourist attractions
        skip_words = ["station", "junction", "railway", "airport", "cantonment", "terminal"]

        if category_preference and any(term in category_preference.lower() for term in ["water", "fall", "falls", "waterfall"]):
            data.sort(key=lambda x: 0 if "fall" in x.get("name", "").lower() or "waterfall" in x.get("name", "").lower() else 1)

        for place in data:
            name = place.get("name", "").strip()
            
            # 1. Skip junk entries
            if not name or len(name) <= 2:
                continue
                
            # 2. Skip transport hubs
            name_lower = name.lower()
            if any(word in name_lower for word in skip_words):
                continue
                
            # 3. Fuzzy deduplication (e.g., "Agra Fort" == "agra fort" == "agrafort")
            normalized_name = "".join(c for c in name_lower if c.isalnum())
            if normalized_name in seen_names:
                continue
                
            seen_names.add(normalized_name)
            
            category = place.get("kinds", "general").split(",")[0] if place.get("kinds") else "general"
            
            attractions.append({
                "name": name,
                "category": category
            })
            
            if len(attractions) >= 10:
                break

        if not attractions:
            return {"error": "No attractions found from API"}

        return {
            "location": location,
            "attractions": attractions
        }

    except requests.exceptions.Timeout:
        return {"error": "Attraction API timed out"}
    except Exception as e:
        return {"error": str(e)}