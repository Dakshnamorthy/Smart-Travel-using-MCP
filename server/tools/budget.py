def estimate_budget(days: int, distance_km: float, people: int, budget_type: str = "medium", explicit_travel_cost: float = None):
    """Estimate a generic budget for a trip."""
    try:
        days = int(days)
        distance_km = float(distance_km)
        people = int(people)
        budget_type = budget_type.lower()

        # -------------------------------
        # Cost configuration
        # -------------------------------
        travel_cost_per_km = {
            "low": 4,
            "medium": 12,
            "high": 30
        }

        food_cost_per_day = {
            "low": 300,
            "medium": 600,
            "high": 1200
        }

        stay_cost_per_night = {
            "low": 800,
            "medium": 2000,
            "high": 5000
        }

        if budget_type not in travel_cost_per_km:
            return {"error": "Invalid budget type (low/medium/high)"}

        # -------------------------------
        # Travel Cost
        # -------------------------------
        if explicit_travel_cost is not None:
            travel_cost = explicit_travel_cost
        else:
            travel_cost = distance_km * travel_cost_per_km[budget_type]

        # -------------------------------
        # Food Cost
        # -------------------------------
        food_cost = days * people * food_cost_per_day[budget_type]

        # -------------------------------
        # Stay Cost
        # -------------------------------
        stay_cost = (days - 1) * stay_cost_per_night[budget_type]

        # -------------------------------
        # Total Cost
        # -------------------------------
        total_cost = round(travel_cost + food_cost + stay_cost, 2)

        return {
            "days": days,
            "people": people,
            "budget_type": budget_type,
            "travel_cost": round(travel_cost, 2),
            "food_cost": food_cost,
            "stay_cost": stay_cost,
            "total_cost": total_cost
        }

    except Exception as e:
        return {"error": str(e)}