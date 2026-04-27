"""
Transport Tool
==============
Estimates transport options and costs between two locations.
Depends on: distance_tool
"""


def transport_tool(origin: str, destination: str, budget: int = None, people: int = 1):
    """Estimate transport options between two locations."""

    try:
        from server.tools.distance import distance_tool

        distance_data = distance_tool(origin, destination)

        if "error" in distance_data:
            return {"error": f"Distance lookup failed: {distance_data['error']}"}

        distance = distance_data["distance_km"]
        people = max(people or 1, 1)

        options = []

        # ------- BUS -------
        bus_cost = distance * 1.2
        options.append({
            "mode": "bus",
            "cost_per_person": round(bus_cost),
            "total_cost": round(bus_cost * people),
            "duration_hours": round(distance / 40, 1),
            "comfort": "low"
        })

        # ------- TRAIN -------
        train_cost = distance * 1.5
        options.append({
            "mode": "train",
            "cost_per_person": round(train_cost),
            "total_cost": round(train_cost * people),
            "duration_hours": round(distance / 60, 1),
            "comfort": "medium"
        })

        # ------- CAB -------
        cab_cost = distance * 12
        options.append({
            "mode": "cab",
            "cost_per_person": round(cab_cost / people),
            "total_cost": round(cab_cost),
            "duration_hours": round(distance / 50, 1),
            "comfort": "high"
        })

        # ------- FLIGHT (only long distance) -------
        if distance > 300:
            flight_cost = distance * 4
            options.append({
                "mode": "flight",
                "cost_per_person": round(flight_cost),
                "total_cost": round(flight_cost * people),
                "duration_hours": round(distance / 500, 1),
                "comfort": "high"
            })

        # Filter by budget if provided
        if budget:
            affordable = [o for o in options if o["total_cost"] <= budget]
            if affordable:
                options = affordable

        return {
            "origin": origin,
            "destination": destination,
            "distance_km": distance,
            "people": people,
            "options": options
        }

    except Exception as e:
        return {"error": str(e)}