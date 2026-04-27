from server.tools.tool_wrapper import safe_call
from server.tools.attraction import attraction_tool
from server.tools.route_optimizer import route_optimizer_tool
from server.tools.hotel import hotel_tool
from server.tools.restaurant import restaurant_tool
from server.tools.fallback_data import (
    get_attraction_fallback,
    get_hotel_fallback,
    get_restaurant_fallback,
)
from server.utils.logger import get_logger

logger = get_logger(__name__)

class PlannerAgent:
    """Agent responsible for selecting places, organizing routes, and picking hotels and restaurants."""
    
    def fetch_attractions(self, dest, category_preference, specific_places):
        logger.info(f"PlannerAgent: Fetching attractions for {dest}")
        attr_result = safe_call(
            tool_fn=attraction_tool,
            tool_name="attraction",
            fallback_fn=lambda: {"location": dest, "attractions": get_attraction_fallback(dest)},
            location=dest,
            category_preference=category_preference
        )
        
        attractions = []
        if attr_result["success"]:
            attractions = attr_result["data"].get("attractions", [])
            
        place_names = []
        for p in attractions:
            if isinstance(p, dict):
                place_names.append(p.get("name", ""))
            else:
                place_names.append(str(p))
        place_names = [n for n in place_names if n]
        
        # Inject user's specific places
        if specific_places and isinstance(specific_places, list):
            for p in specific_places:
                if str(p).lower() not in [x.lower() for x in place_names]:
                    place_names.insert(0, str(p))
                    
        return place_names, attr_result["source"]

    def optimize_route(self, dest, place_names, days):
        logger.info(f"PlannerAgent: Optimizing route for {len(place_names)} places over {days} days")
        import math
        max_per_day = max(2, math.ceil(len(place_names) / max(days, 1))) if days and len(place_names) > 0 else 4
        
        route_result = safe_call(
            tool_fn=route_optimizer_tool,
            tool_name="route_optimizer",
            places=place_names,
            base_location=dest,
            max_per_day=max_per_day
        )
        
        if route_result["success"]:
            data = route_result["data"]
            return data.get("optimized_route", place_names), data.get("daily_plan", None), data.get("estimated_days", days)
        return place_names, None, days

    def fetch_hotels(self, dest, budget_str, near_location=None):
        logger.info(f"PlannerAgent: Fetching hotels for {dest}" + (f" near {near_location}" if near_location else ""))
        hotel_result = safe_call(
            tool_fn=hotel_tool,
            tool_name="hotel",
            fallback_fn=lambda: {"location": dest, "budget": budget_str, "hotels": get_hotel_fallback(dest)},
            location=dest,
            budget=budget_str,
            near_location=near_location
        )
        return hotel_result["data"].get("hotels", []) if hotel_result["success"] else [], hotel_result["source"]

    def fetch_restaurants(self, dest, near_location=None):
        logger.info(f"PlannerAgent: Fetching restaurants for {dest}" + (f" near {near_location}" if near_location else ""))
        rest_result = safe_call(
            tool_fn=restaurant_tool,
            tool_name="restaurant",
            fallback_fn=lambda: {"location": dest, "restaurants": get_restaurant_fallback(dest)},
            location=dest,
            near_location=near_location
        )
        
        restaurants = []
        if rest_result["success"]:
            for r in rest_result["data"].get("restaurants", []):
                if isinstance(r, dict):
                    restaurants.append(r.get("name", str(r)))
                else:
                    restaurants.append(str(r))
        return restaurants, rest_result["source"]
