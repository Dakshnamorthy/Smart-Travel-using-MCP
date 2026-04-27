from server.tools.tool_wrapper import safe_call
from server.tools.transport import transport_tool
from server.tools.budget import estimate_budget
from server.utils.logger import get_logger

logger = get_logger(__name__)

class FinanceAgent:
    """Agent responsible for calculating travel costs, transport options, and overall budgets."""
    
    def calculate_transport(self, source, dest, budget, people):
        if not source:
            return None
        logger.info(f"FinanceAgent: Calculating transport from {source} to {dest}")
        transport_result = safe_call(
            tool_fn=transport_tool,
            tool_name="transport",
            origin=source,
            destination=dest,
            budget=budget,
            people=people
        )
        if transport_result["success"]:
            return transport_result["data"]
        return None

    def estimate_budget(self, days, people, budget, transport_data, t_mode):
        logger.info(f"FinanceAgent: Estimating total budget")
        distance_km = 300
        explicit_travel_cost = None
        
        if transport_data:
            distance_km = transport_data.get("distance_km", 0)
            if t_mode:
                for opt in transport_data.get("options", []):
                    if opt["mode"].lower() == t_mode:
                        explicit_travel_cost = opt.get("total_cost")
                        break

        budget_type = "medium"
        if budget:
            per_person = budget / max(people, 1)
            if per_person < 5000:
                budget_type = "low"
            elif per_person < 15000:
                budget_type = "medium"
            else:
                budget_type = "high"

        budget_result = safe_call(
            tool_fn=estimate_budget,
            tool_name="budget",
            days=days,
            distance_km=distance_km,
            people=people,
            budget_type=budget_type,
            explicit_travel_cost=explicit_travel_cost
        )
        
        if budget_result["success"]:
            return budget_result["data"], budget_type
        return None, budget_type
