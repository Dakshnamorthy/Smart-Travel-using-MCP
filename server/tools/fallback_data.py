"""
Fallback Data Registry
======================
Location-aware fallback data for when APIs fail.
Each tool has its own fallback function that returns realistic data
based on the destination city.

WHY: Without this, tools return hardcoded Chennai data for every city.
     That's silent hallucination — the worst kind of bug in an MCP system.
"""


# ============================================================
# ATTRACTION FALLBACKS
# ============================================================
ATTRACTION_FALLBACKS = {
    "chennai": [
        {"name": "Marina Beach", "category": "beach"},
        {"name": "Kapaleeswarar Temple", "category": "temple"},
        {"name": "Fort St. George", "category": "historical"},
        {"name": "San Thome Basilica", "category": "church"},
        {"name": "Government Museum", "category": "museum"},
    ],
    "mumbai": [
        {"name": "Gateway of India", "category": "monument"},
        {"name": "Marine Drive", "category": "promenade"},
        {"name": "Elephanta Caves", "category": "historical"},
        {"name": "Chhatrapati Shivaji Terminus", "category": "historical"},
        {"name": "Juhu Beach", "category": "beach"},
    ],
    "delhi": [
        {"name": "Red Fort", "category": "monument"},
        {"name": "India Gate", "category": "monument"},
        {"name": "Qutub Minar", "category": "historical"},
        {"name": "Lotus Temple", "category": "temple"},
        {"name": "Humayun's Tomb", "category": "historical"},
    ],
    "goa": [
        {"name": "Baga Beach", "category": "beach"},
        {"name": "Basilica of Bom Jesus", "category": "church"},
        {"name": "Fort Aguada", "category": "historical"},
        {"name": "Dudhsagar Falls", "category": "waterfall"},
        {"name": "Anjuna Flea Market", "category": "market"},
    ],
    "jaipur": [
        {"name": "Hawa Mahal", "category": "monument"},
        {"name": "Amber Fort", "category": "fort"},
        {"name": "City Palace", "category": "palace"},
        {"name": "Jantar Mantar", "category": "observatory"},
        {"name": "Nahargarh Fort", "category": "fort"},
    ],
    "munnar": [
        {"name": "Eravikulam National Park", "category": "nature"},
        {"name": "Tea Museum", "category": "museum"},
        {"name": "Mattupetty Dam", "category": "scenic"},
        {"name": "Top Station", "category": "viewpoint"},
        {"name": "Attukal Waterfalls", "category": "waterfall"},
    ],
    "pondicherry": [
        {"name": "Promenade Beach", "category": "beach"},
        {"name": "Auroville", "category": "spiritual"},
        {"name": "Paradise Beach", "category": "beach"},
        {"name": "French Quarter", "category": "heritage"},
        {"name": "Basilica of the Sacred Heart", "category": "church"},
    ],
    "wayanad": [
        {"name": "Edakkal Caves", "category": "historical"},
        {"name": "Banasura Sagar Dam", "category": "scenic"},
        {"name": "Chembra Peak", "category": "trekking"},
        {"name": "Soochipara Falls", "category": "waterfall"},
        {"name": "Wayanad Wildlife Sanctuary", "category": "nature"},
    ],
    "bangalore": [
        {"name": "Lalbagh Botanical Garden", "category": "garden"},
        {"name": "Cubbon Park", "category": "park"},
        {"name": "Bangalore Palace", "category": "palace"},
        {"name": "Vidhana Soudha", "category": "landmark"},
        {"name": "ISKCON Temple", "category": "temple"},
    ],
    "hyderabad": [
        {"name": "Charminar", "category": "monument"},
        {"name": "Golconda Fort", "category": "fort"},
        {"name": "Hussain Sagar Lake", "category": "lake"},
        {"name": "Ramoji Film City", "category": "entertainment"},
        {"name": "Salar Jung Museum", "category": "museum"},
    ],
    "udaipur": [
        {"name": "City Palace Udaipur", "category": "palace"},
        {"name": "Lake Pichola", "category": "lake"},
        {"name": "Jag Mandir", "category": "palace"},
        {"name": "Saheliyon-ki-Bari", "category": "garden"},
        {"name": "Fateh Sagar Lake", "category": "lake"},
    ],
    "varanasi": [
        {"name": "Dashashwamedh Ghat", "category": "ghat"},
        {"name": "Kashi Vishwanath Temple", "category": "temple"},
        {"name": "Assi Ghat", "category": "ghat"},
        {"name": "Sarnath", "category": "historical"},
        {"name": "Ramnagar Fort", "category": "fort"},
    ],
}


# ============================================================
# RESTAURANT FALLBACKS
# ============================================================
RESTAURANT_FALLBACKS = {
    "chennai": ["Saravana Bhavan", "Murugan Idli Shop", "Sangeetha Veg Restaurant", "Annalakshmi", "Barbeque Nation"],
    "mumbai": ["Leopold Cafe", "Trishna", "Britannia & Co", "Bademiya", "Cafe Mondegar"],
    "delhi": ["Karim's", "Bukhara", "Paranthe Wali Gali", "Indian Accent", "Saravana Bhavan"],
    "goa": ["Britto's", "Fisherman's Wharf", "Martin's Corner", "Gunpowder", "Thalassa"],
    "jaipur": ["Laxmi Mishthan Bhandar", "Chokhi Dhani", "Rawat Mishthan Bhandar", "Tapri Central", "Suvarna Mahal"],
    "munnar": ["Saravana Bhavan Munnar", "Rapsy Restaurant", "SN Restaurant", "Al Buhari", "Silver Spoon"],
    "pondicherry": ["Villa Shanti", "Le Dupleix", "Cafe des Arts", "Baker Street", "Surguru"],
    "wayanad": ["Jubilee Restaurant", "Hotel Regency", "1st Wayanadan", "Malabar Kitchen", "Hotel Haritha"],
    "bangalore": ["MTR", "Vidyarthi Bhavan", "Toit", "Meghana Foods", "Koshy's"],
    "hyderabad": ["Paradise Biryani", "Bawarchi", "Shah Ghouse", "Pista House", "Chutneys"],
}


# ============================================================
# HOTEL FALLBACKS
# ============================================================
HOTEL_FALLBACKS = {
    "chennai": [
        {"name": "Taj Connemara", "price": "₹7000+", "tier": "luxury"},
        {"name": "GRT Grand", "price": "₹3000-5000", "tier": "mid"},
        {"name": "FabHotel Prime", "price": "₹1000-2500", "tier": "budget"},
    ],
    "mumbai": [
        {"name": "Taj Mahal Palace", "price": "₹15000+", "tier": "luxury"},
        {"name": "Hotel Marine Plaza", "price": "₹5000-8000", "tier": "mid"},
        {"name": "Hotel City King", "price": "₹1500-3000", "tier": "budget"},
    ],
    "delhi": [
        {"name": "The Imperial", "price": "₹12000+", "tier": "luxury"},
        {"name": "The Claridges", "price": "₹5000-8000", "tier": "mid"},
        {"name": "Hotel Palace Heights", "price": "₹2000-4000", "tier": "budget"},
    ],
    "goa": [
        {"name": "Taj Fort Aguada", "price": "₹10000+", "tier": "luxury"},
        {"name": "Cidade de Goa", "price": "₹4000-7000", "tier": "mid"},
        {"name": "OYO Goa", "price": "₹800-2000", "tier": "budget"},
    ],
    "jaipur": [
        {"name": "Rambagh Palace", "price": "₹20000+", "tier": "luxury"},
        {"name": "Samode Haveli", "price": "₹5000-9000", "tier": "mid"},
        {"name": "Hotel Pearl Palace", "price": "₹1000-2500", "tier": "budget"},
    ],
    "munnar": [
        {"name": "Windermere Estate", "price": "₹6000+", "tier": "luxury"},
        {"name": "Tea County", "price": "₹2500-4500", "tier": "mid"},
        {"name": "Green Valley Vista", "price": "₹800-1800", "tier": "budget"},
    ],
    "pondicherry": [
        {"name": "Palais de Mahe", "price": "₹6000+", "tier": "luxury"},
        {"name": "Hotel De L'Orient", "price": "₹3000-5000", "tier": "mid"},
        {"name": "Maison Perumal", "price": "₹1500-3000", "tier": "budget"},
    ],
    "wayanad": [
        {"name": "Vythiri Resort", "price": "₹8000+", "tier": "luxury"},
        {"name": "Wayanad Silverwoods", "price": "₹2500-4000", "tier": "mid"},
        {"name": "Pepper Trail", "price": "₹1000-2000", "tier": "budget"},
    ],
    "bangalore": [
        {"name": "The Leela Palace", "price": "₹12000+", "tier": "luxury"},
        {"name": "Taj MG Road", "price": "₹5000-8000", "tier": "mid"},
        {"name": "Treebo Trend", "price": "₹1500-3000", "tier": "budget"},
    ],
    "hyderabad": [
        {"name": "Taj Falaknuma Palace", "price": "₹20000+", "tier": "luxury"},
        {"name": "ITC Kohenur", "price": "₹6000-10000", "tier": "mid"},
        {"name": "Treebo Trip", "price": "₹1000-2500", "tier": "budget"},
    ],
}


# ============================================================
# WEATHER FALLBACKS
# ============================================================
WEATHER_FALLBACKS = {
    "chennai": {"temperature": 32, "description": "hot and humid", "humidity": 75},
    "mumbai": {"temperature": 30, "description": "warm and humid", "humidity": 80},
    "delhi": {"temperature": 28, "description": "warm", "humidity": 50},
    "goa": {"temperature": 31, "description": "tropical warm", "humidity": 70},
    "jaipur": {"temperature": 30, "description": "dry and warm", "humidity": 35},
    "munnar": {"temperature": 20, "description": "cool and pleasant", "humidity": 65},
    "pondicherry": {"temperature": 31, "description": "coastal warm", "humidity": 72},
    "wayanad": {"temperature": 22, "description": "cool and misty", "humidity": 70},
    "bangalore": {"temperature": 25, "description": "pleasant", "humidity": 55},
    "hyderabad": {"temperature": 29, "description": "warm", "humidity": 50},
}


# ============================================================
# GETTER FUNCTIONS
# ============================================================

def get_attraction_fallback(location: str) -> list:
    """Get fallback attractions for a location."""
    key = location.lower().strip()
    if key in ATTRACTION_FALLBACKS:
        return ATTRACTION_FALLBACKS[key]
    # Generic fallback — clearly labeled
    return [
        {"name": f"Popular Attraction 1 in {location}", "category": "general"},
        {"name": f"Popular Attraction 2 in {location}", "category": "general"},
        {"name": f"Heritage Site in {location}", "category": "historical"},
        {"name": f"Local Market in {location}", "category": "market"},
        {"name": f"Nature Spot near {location}", "category": "nature"},
    ]


def get_restaurant_fallback(location: str) -> list:
    """Get fallback restaurants for a location."""
    key = location.lower().strip()
    if key in RESTAURANT_FALLBACKS:
        return RESTAURANT_FALLBACKS[key]
    return [
        f"Local Restaurant 1 in {location}",
        f"Local Restaurant 2 in {location}",
        f"Street Food Corner in {location}",
        f"Family Diner in {location}",
        f"Cafe in {location}",
    ]


def get_hotel_fallback(location: str) -> list:
    """Get fallback hotels for a location."""
    key = location.lower().strip()
    if key in HOTEL_FALLBACKS:
        return HOTEL_FALLBACKS[key]
    return [
        {"name": f"Budget Stay in {location}", "price": "₹1000-2500", "tier": "budget"},
        {"name": f"Standard Hotel in {location}", "price": "₹3000-5000", "tier": "mid"},
        {"name": f"Premium Hotel in {location}", "price": "₹6000+", "tier": "luxury"},
    ]


def get_weather_fallback(location: str) -> dict:
    """Get fallback weather for a location."""
    key = location.lower().strip()
    if key in WEATHER_FALLBACKS:
        return WEATHER_FALLBACKS[key]
    return {"temperature": 28, "description": "typical weather", "humidity": 60}
