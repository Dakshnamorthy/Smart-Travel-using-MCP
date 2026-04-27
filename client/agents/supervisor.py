import json
from client.agents.planner import PlannerAgent
from client.agents.finance import FinanceAgent
from server.utils.logger import get_logger

logger = get_logger(__name__)

class SupervisorAgent:
    """Orchestrates the entire planning process by delegating tasks to sub-agents."""
    
    def __init__(self, llm_function):
        self.planner = PlannerAgent()
        self.finance = FinanceAgent()
        self.safe_llm = llm_function

    def plan_trip(self, state, estimate_days_func):
        dest = state.get("destination")
        if not dest:
            return "📍 Please provide a destination. Example: 'Plan a trip from Chennai to Goa for 3 people budget 15000'"

        source = state.get("source")
        budget = state.get("budget")
        people = state.get("people") or 1
        t_mode = state.get("transport_mode")
        category_preference = state.get("category_preference")
        specific_places = state.get("specific_places")
        
        days = state.get("days")
        if days:
            logger.info(f"Supervisor: User Override for {days} days.")
        else:
            days = estimate_days_func(budget, people)

        logger.info(f"Supervisor: Planning {days}-day trip to {dest} from {source}")

        # 1. Delegate to Planner Agent
        place_names, attr_source = self.planner.fetch_attractions(dest, category_preference, specific_places)
        
        route, daily_plan, est_days = self.planner.optimize_route(dest, place_names, days)
        if not state.get("days") and est_days > days:
            days = est_days
            logger.info(f"Supervisor: Auto-adjusted to {days} days")

        # Use first attraction as reference for hotel/restaurant proximity search
        near_attraction = route[0] if route else None
        hotels, hotel_source = self.planner.fetch_hotels(dest, str(budget), near_location=near_attraction)
        restaurants, rest_source = self.planner.fetch_restaurants(dest, near_location=near_attraction)

        # 2. Delegate to Finance Agent
        transport_data = self.finance.calculate_transport(source, dest, budget, people)
        budget_info, budget_type = self.finance.estimate_budget(days, people, budget, transport_data, t_mode)

        # 3. Format result
        structured = {
            "destination": dest,
            "source": source,
            "days": days,
            "people": people,
            "route": route[:10] if route else [],
            "daily_plan": daily_plan,
            "hotels": hotels[:5],
            "restaurants": restaurants[:5],
            "transport": transport_data,
            "budget": budget_info,
        }

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert travel planner creating an immersive and spatial daily itinerary.\n"
                    "You will receive structured JSON detailing the destination, budget, routed plan, hotels, and restaurants.\n\n"
                    "CRITICAL INSTRUCTIONS:\n"
                    "1. DO NOT just dump restaurants and hotels at the bottom of the response.\n"
                    "2. INTEGRATE the recommended restaurants organically into the Lunch and Dinner segments of the daily plan.\n"
                    "3. INTEGRATE the hotel natively into the Day 1 morning slot (e.g., 'Arrive and check-in to [Hotel Name]').\n"
                    "4. Format the itinerary cleanly using regular spacing. Never use asterisks or hashes. Do not bold text.\n"
                    "5. Only use the places/hotels/restaurants provided in the data. Do NOT hallucinate new venues.\n"
                    "6. Conclude with a clear Cost Summary using the budget data provided.\n"
                )
            },
            {
                "role": "user",
                "content": json.dumps(structured, indent=2)
            }
        ]

        try:
            res = self.safe_llm(messages)
            final_response = res.choices[0].message.content
            final_response = final_response.replace("*", "").replace("#", "")

            sources_used = []
            if attr_source == "fallback": sources_used.append("attractions (local database)")
            if hotel_source == "fallback": sources_used.append("hotels (local database)")
            if rest_source == "fallback": sources_used.append("restaurants (local database)")

            if sources_used:
                final_response += f"\n\n📌 Note: Some data came from our local database: {', '.join(sources_used)}"

            return final_response
        except Exception as e:
            logger.error(f"LLM failed to generate itinerary: {e}")
            return f"❌ LLM failed to generate itinerary: {str(e)}"
