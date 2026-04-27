"""
Route Optimizer Tool
====================
Optimizes visit order using Nearest Neighbor algorithm.

HOW IT WORKS:
  1. Geocode all places to get lat/lon coordinates
  2. Build a distance matrix between all places (using Haversine - fast, no API needed)
  3. Apply Nearest Neighbor: start at first place, always visit the closest unvisited next
  4. Group into days: max N places per day, with morning/afternoon/evening slots

WHY Nearest Neighbor:
  - Simple, fast, works well for small sets (5-15 places)
  - Avoids zig-zag routes
  - No external API needed (uses math only)
  - For 10 places, it's near-optimal in practice

WHY NOT brute force:
  - 10 places = 3,628,800 permutations — too slow
  - Nearest Neighbor gives ~80% optimal solution instantly
"""

import math
import requests


# ============================================================
# HAVERSINE DISTANCE (fast, no API needed)
# ============================================================
def haversine(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance between two points in km."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


# ============================================================
# GEOCODE PLACES (batch)
# ============================================================
def geocode_places(places, base_location=None):
    """
    Get coordinates for a list of place names.
    Appends base_location to improve geocoding accuracy.
    Returns: list of {"name", "lat", "lon"} dicts
    """
    headers = {"User-Agent": "smart-travel-mcp-agent"}
    results = []

    for place in places:
        try:
            # Search with city context for better accuracy
            query = f"{place}, {base_location}" if base_location else place

            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                headers=headers,
                params={"q": query, "format": "json"},
                timeout=5
            )

            data = response.json()

            if data:
                results.append({
                    "name": place,
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"])
                })
            else:
                # Can't geocode — skip but keep track
                results.append({
                    "name": place,
                    "lat": None,
                    "lon": None
                })

        except Exception:
            results.append({
                "name": place,
                "lat": None,
                "lon": None
            })

    return results


# ============================================================
# NEAREST NEIGHBOR ALGORITHM
# ============================================================
def nearest_neighbor_route(geocoded_places):
    """
    Apply Nearest Neighbor algorithm to find an efficient visit order.

    Algorithm:
      1. Start at the first place
      2. From current place, find the nearest unvisited place
      3. Move there, mark as visited
      4. Repeat until all places are visited

    Returns: reordered list of place names + total distance
    """
    # Filter out places we couldn't geocode
    valid = [p for p in geocoded_places if p["lat"] is not None]
    invalid = [p for p in geocoded_places if p["lat"] is None]

    if len(valid) <= 1:
        return [p["name"] for p in geocoded_places], 0

    # Build distance matrix
    n = len(valid)
    dist_matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(valid[i]["lat"], valid[i]["lon"],
                          valid[j]["lat"], valid[j]["lon"])
            dist_matrix[i][j] = d
            dist_matrix[j][i] = d

    # Nearest Neighbor starting from index 0
    visited = [False] * n
    route_indices = [0]
    visited[0] = True
    total_distance = 0

    for _ in range(n - 1):
        current = route_indices[-1]
        nearest_idx = -1
        nearest_dist = float("inf")

        for j in range(n):
            if not visited[j] and dist_matrix[current][j] < nearest_dist:
                nearest_dist = dist_matrix[current][j]
                nearest_idx = j

        if nearest_idx != -1:
            route_indices.append(nearest_idx)
            visited[nearest_idx] = True
            total_distance += nearest_dist

    # Build ordered result
    optimized = [valid[i]["name"] for i in route_indices]

    # Add back ungeocodable places at the end
    optimized.extend([p["name"] for p in invalid])

    return optimized, round(total_distance, 2)


# ============================================================
# DAY GROUPER
# ============================================================
def group_into_days(places, max_per_day=4):
    """
    Group places into day-wise slots.
    Each day gets morning/afternoon/evening assignments.

    Args:
        places: ordered list of place names
        max_per_day: max places per day (default 4 — realistic for sightseeing)

    Returns: list of day dicts
    """
    days = []
    slots = ["morning", "afternoon", "afternoon", "evening"]

    for i in range(0, len(places), max_per_day):
        day_places = places[i:i + max_per_day]
        day = {"day": len(days) + 1, "places": []}

        for j, place in enumerate(day_places):
            slot = slots[j] if j < len(slots) else "evening"
            day["places"].append({
                "name": place,
                "time_slot": slot
            })

        days.append(day)

    return days


# ============================================================
# MAIN TOOL FUNCTION
# ============================================================
def route_optimizer_tool(places, base_location=None, max_per_day=4):
    """
    Optimize visit order for a list of places using Nearest Neighbor.

    Args:
        places:         List of place name strings
        base_location:  City name (improves geocoding accuracy)
        max_per_day:    Max places per day

    Returns:
        {
            "optimized_route": [...],
            "daily_plan": [{day: 1, places: [...]}, ...],
            "total_distance_km": float,
            "total_places": int,
            "estimated_days": int
        }
    """
    if not places:
        return {
            "optimized_route": [],
            "daily_plan": [],
            "total_distance_km": 0,
            "total_places": 0,
            "estimated_days": 0,
            "note": "No places provided"
        }

    # If only 1-2 places, no optimization needed
    if len(places) <= 2:
        daily_plan = group_into_days(places, max_per_day)
        return {
            "optimized_route": places,
            "daily_plan": daily_plan,
            "total_distance_km": 0,
            "total_places": len(places),
            "estimated_days": len(daily_plan),
            "note": "Too few places for optimization"
        }

    # Step 1: Geocode all places
    geocoded = geocode_places(places, base_location)

    # Count how many we could geocode
    geocoded_count = sum(1 for p in geocoded if p["lat"] is not None)

    if geocoded_count < 2:
        # Can't optimize without coordinates — return original order
        daily_plan = group_into_days(places, max_per_day)
        return {
            "optimized_route": places,
            "daily_plan": daily_plan,
            "total_distance_km": 0,
            "total_places": len(places),
            "estimated_days": len(daily_plan),
            "note": "Could not geocode enough places for optimization"
        }

    # Step 2: Apply Nearest Neighbor
    optimized, total_distance = nearest_neighbor_route(geocoded)

    # Step 3: Group into days
    daily_plan = group_into_days(optimized, max_per_day)

    return {
        "optimized_route": optimized,
        "daily_plan": daily_plan,
        "total_distance_km": total_distance,
        "total_places": len(optimized),
        "estimated_days": len(daily_plan),
        "geocoded_count": geocoded_count,
        "note": f"Optimized using Nearest Neighbor ({geocoded_count}/{len(places)} places geocoded)"
    }