"""
Settings
========
Central configuration for the Smart Travel Planner MCP Agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# API Keys
# ============================================================
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY")
ORS_API_KEY = os.getenv("ORS_API_KEY")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ============================================================
# Tool Registry — all available tools
# ============================================================
TOOL_NAMES = [
    "weather",
    "geocode",
    "attraction",
    "restaurant",
    "hotel",
    "distance",
    "transport",
    "route_optimizer",
    "budget",
    "currency",
    "itinerary",
    "summary",
    "save_trip",
]

# ============================================================
# Location Normalization Map
# ============================================================
LOCATION_ALIASES = {
    "pondy": "Pondicherry",
    "pondicherry": "Pondicherry",
    "puducherry": "Pondicherry",
    "munnar": "Munnar",
    "wayanad": "Wayanad",
    "chennai": "Chennai",
    "madras": "Chennai",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "goa": "Goa",
    "jaipur": "Jaipur",
    "bangalore": "Bangalore",
    "bengaluru": "Bangalore",
    "hyderabad": "Hyderabad",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "udaipur": "Udaipur",
    "varanasi": "Varanasi",
    "benaras": "Varanasi",
    "kashi": "Varanasi",
    "ooty": "Ooty",
    "kodaikanal": "Kodaikanal",
    "shimla": "Shimla",
    "manali": "Manali",
    "darjeeling": "Darjeeling",
    "agra": "Agra",
    "mysore": "Mysore",
    "mysuru": "Mysore",
    "coorg": "Coorg",
    "alleppey": "Alleppey",
    "alappuzha": "Alleppey",
    "kochi": "Kochi",
    "cochin": "Kochi",
}
