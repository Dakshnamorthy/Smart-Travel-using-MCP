"""
Smart Travel Planner — MCP Server
==================================
Registers all tools with FastMCP for remote tool access.
"""

from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

from tools.weather import weather_tool
from tools.geocode import geocode_tool
from tools.attraction import attraction_tool
from tools.restaurant import restaurant_tool
from tools.hotel import hotel_tool
from tools.distance import distance_tool
from tools.route_optimizer import route_optimizer_tool
from tools.transport import transport_tool
from tools.budget import estimate_budget
from tools.currency import convert_currency
from tools.knowledge_rag import query_knowledge

mcp = FastMCP("Smart Travel Planner MCP")



@mcp.tool()
def weather(location: str):
    """Get current weather for a location."""
    return weather_tool(location)


@mcp.tool()
def geocode(location: str):
    """Convert location name to coordinates."""
    return geocode_tool(location)


@mcp.tool()
def attraction(location: str, category_preference: str = None):
    """Get top attractions for a location. You can specify a category_preference like 'beaches' or 'historical'."""
    return attraction_tool(location, category_preference)


@mcp.tool()
def restaurant(location: str):
    """Get nearby restaurants for a location."""
    return restaurant_tool(location)


@mcp.tool()
def hotel(location: str, budget: str = "medium"):
    """Get hotel recommendations for a location."""
    return hotel_tool(location, budget)


@mcp.tool()
def distance(origin: str, destination: str):
    """Calculate distance between two locations."""
    return distance_tool(origin, destination)


@mcp.tool()
def route_optimizer(places: list, base_location: str = None, max_per_day: int = 4):
    """Optimize visit order for a list of places."""
    return route_optimizer_tool(places, base_location, max_per_day)


@mcp.tool()
def transport(origin: str, destination: str, budget: int = None, people: int = 1):
    """Get transport options between two locations."""
    return transport_tool(origin, destination, budget, people)


@mcp.tool()
def budget(days: int, distance_km: float, people: int, budget_type: str = "medium", explicit_travel_cost: float = None):
    """Estimate trip budget breakdown."""
    return estimate_budget(days, distance_km, people, budget_type, explicit_travel_cost)


@mcp.tool()
def currency(amount: float, from_currency: str, to_currency: str):
    """Convert currency from one to another."""
    return convert_currency(amount, from_currency, to_currency)

@mcp.tool()
def knowledge_rag(query: str):
    """Query the local travel knowledge base for general travel facts and tips."""
    return query_knowledge(query)


if __name__ == "__main__":
    mcp.run()