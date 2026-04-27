"""
Smart Travel Planner — MCP Client
==================================
Architecture: User → Intent Router → Handler → Tool Orchestration → LLM (formatting only)

Key Principles:
  - LLM is NOT allowed to hallucinate
  - Tools are the ONLY source of truth
  - LLM is used ONLY for formatting responses
  - Every tool call goes through safe_call() wrapper
"""

# ============================================================
# IMPORTS
# ============================================================
import sys
import os
import json
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure the local package directory does not shadow the root 'client' package
if script_dir in sys.path:
    sys.path.remove(script_dir)

from groq import Groq, RateLimitError
from dotenv import load_dotenv

# Logger
from server.utils.logger import get_logger
logger = get_logger(__name__)

# Tools
from server.tools.weather import weather_tool
from server.tools.geocode import geocode_tool
from server.tools.attraction import attraction_tool
from server.tools.restaurant import restaurant_tool
from server.tools.hotel import hotel_tool
from server.tools.distance import distance_tool
from server.tools.route_optimizer import route_optimizer_tool
from server.tools.transport import transport_tool
from server.tools.budget import estimate_budget
from server.tools.currency import convert_currency
from server.tools.itinerary import generate_itinerary
from server.tools.summary import generate_trip_summary
from server.tools.save_trip import save_trip

from client.agents.supervisor import SupervisorAgent
from server.tools.knowledge_rag import query_knowledge


# Reliability Layer
from server.tools.tool_wrapper import safe_call
from server.tools.fallback_data import (
    get_attraction_fallback,
    get_restaurant_fallback,
    get_hotel_fallback,
    get_weather_fallback,
)

# Config
from config.settings import LOCATION_ALIASES, GROQ_MODEL

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ============================================================
# PLANNING STATE + CONVERSATION CONTEXT
# ============================================================
planning_state = {
    "source": None,
    "destination": None,
    "budget": None,
    "people": None,
}

# Tracks the last mentioned location across ALL queries
# WHY: If user asks "weather in wayanad" then says "plan a trip",
#      the system should remember wayanad as the destination.
conversation_context = {
    "last_location": None,
    "history": [],  # recent queries for context
}


# ============================================================
# SAFE LLM CALL
# ============================================================
def safe_llm(messages):
    """Call LLM with retry on rate limit."""
    logger.info({
        "event": "llm_request",
        "model": GROQ_MODEL,
        "message_count": len(messages)
    })
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages
        )
        logger.info({
            "event": "llm_response",
            "model": GROQ_MODEL,
            "response_tokens": response.usage.total_tokens if hasattr(response, 'usage') else None
        })
        return response
    except RateLimitError:
        logger.warning("[Rate limit hit — waiting 3s...]")
        time.sleep(3)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages
        )
        logger.info({
            "event": "llm_response_after_retry",
            "model": GROQ_MODEL
        })
        return response


# ============================================================
# LOCATION NORMALIZATION
# ============================================================
def normalize_location(name):
    """Normalize location name using alias map."""
    if not name:
        return name
    if isinstance(name, list):
        name = name[0] if name else ""
    if not isinstance(name, str) or not name:
        return ""
    clean = name.strip().lower()
    # Remove common punctuation
    clean = clean.rstrip(".,!?")
    if clean in LOCATION_ALIASES:
        return LOCATION_ALIASES[clean]
    return name.strip().title()


# ============================================================
# LLM-BASED INTENT + ENTITY EXTRACTION (Primary)
# ============================================================
def llm_classify_and_extract(user_input):
    """
    Use LLM to classify intent AND extract entities in ONE call.

    WHY LLM instead of if-else:
    - "plan a trip for wayanad" → if-else misses destination (no "to" keyword)
    - "I want to visit goa"    → if-else might classify but can't extract well
    - "what's the weather like in pondy" → LLM understands "pondy" = Pondicherry

    Returns: {"intent": str, "destination": str|None, "source": str|None,
             "budget": int|None, "people": int|None, "location": str|None}
    """
    # Build context from conversation history
    context_hint = ""
    if planning_state["destination"]:
        context_hint += f"Previously mentioned destination: {planning_state['destination']}\n"
    if planning_state["source"]:
        context_hint += f"Previously mentioned source: {planning_state['source']}\n"
    if conversation_context["last_location"]:
        context_hint += f"Last mentioned location: {conversation_context['last_location']}\n"
    if planning_state["budget"]:
        context_hint += f"Previously mentioned budget: {planning_state['budget']}\n"
    if planning_state["people"]:
        context_hint += f"Previously mentioned people: {planning_state['people']}\n"

    messages = [
        {
            "role": "system",
            "content": (
                "You are an intent classifier for a travel planner. "
                "Analyze the user query and return ONLY a JSON object (no markdown, no explanation).\n\n"
                "Valid intents: weather, planning, distance, transport, restaurant, hotel, tourist, budget, currency, save, casual, general, off_topic\n\n"
                "Extract these entities from the query:\n"
                "- destination: the place the user wants to go/know about\n"
                "- source: where the user is traveling from (origin)\n"
                "- budget: total budget amount (number only)\n"
                "- people: number of people/members\n"
                "- days: number of days/duration explicitly requested for the trip (number only)\n"
                "- transport_mode: preferred transport mode (e.g. flight, train, bus, cab)\n"
                "- category_preference: preferred category of places (e.g. beaches, religious, historical, nature)\n"
                "- specific_places: list of explicit tourist spots/landmarks the user asked to visit (e.g. ['Dudhsagar Falls', 'Baga Beach'])\n"
                "- location: any location mentioned (for weather/tourist/hotel/restaurant queries)\n\n"
                f"CONVERSATION CONTEXT:\n{context_hint}\n"
                "If the user refers to a previously mentioned location (e.g. 'plan a trip there'), "
                "use the context above to fill in the destination.\n\n"
                "RULES:\n"
                "- Return ONLY valid JSON, no other text\n"
                "- Use null for missing fields\n"
                "- 'casual' intent = greetings, thanks, bye\n"
                "- 'off_topic' intent = questions completely unrelated to travel (e.g. 'write me code', 'solve math', 'who is the president', 'recipe for biryani', 'cricket score')\n"
                "- 'general' intent = travel-related factual questions (e.g. 'history of goa', 'best time to visit manali', 'visa for europe')\n"
                "- ONLY use 'restaurant' or 'tourist' if the user is explicitly asking to FIND places to visit/eat (e.g., 'find me a restaurant', 'best tourist places')\n"
                "- If user says 'plan a trip for X' or 'trip to X' or 'visit X', intent is 'planning' and X is destination\n"
                "- Normalize common nicknames: pondy=Pondicherry, bombay=Mumbai, madras=Chennai, bengaluru=Bangalore\n"
            )
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0,  # deterministic
            max_tokens=200
        )

        raw = response.choices[0].message.content.strip()

        # Clean: remove markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        result = json.loads(raw)

        # Normalize extracted locations
        for key in ["destination", "source", "location"]:
            if result.get(key):
                result[key] = normalize_location(result[key])

        return result

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"[LLM classifier failed: {e} — using keyword fallback]")
        return None


# ============================================================
# KEYWORD-BASED FALLBACK (used when LLM classifier fails)
# ============================================================
def keyword_classify_intent(text):
    """Fallback: classify using keywords when LLM is unavailable."""
    text = text.lower()

    if any(w in text for w in ["weather", "temperature", "climate", "forecast"]):
        return "weather"
    if any(w in text for w in ["plan", "trip", "itinerary", "travel", "visit"]):
        return "planning"
    if any(w in text for w in ["distance", "how far", "km between"]):
        return "distance"
    if any(w in text for w in ["restaurant", "food", "eat", "dining"]):
        return "restaurant"
    if any(w in text for w in ["hotel", "stay", "accommodation", "lodge"]):
        return "hotel"
    if any(w in text for w in ["tourist", "places", "attraction", "sightseeing", "things to do"]):
        return "tourist"
    if any(w in text for w in ["budget", "cost", "expense", "how much"]):
        return "budget"
    if any(w in text for w in ["convert", "currency", "exchange rate"]):
        return "currency"
    if any(w in text for w in ["save", "store", "bookmark"]):
        return "save"
    if text.strip() in ["thanks", "thank you", "ok", "fine", "bye", "goodbye"]:
        return "casual"
    return "general"


def keyword_extract_state(text):
    """Fallback: extract entities using keyword patterns."""
    words = text.lower().split()

    for keyword in ["to", "for", "in", "at"]:
        if keyword in words:
            idx = words.index(keyword)
            if idx + 1 < len(words):
                loc = normalize_location(words[idx + 1])
                if loc and loc.lower() not in ["a", "the", "my", "our", "trip", "people", "person"]:
                    if keyword in ["to", "for"]:
                        planning_state["destination"] = loc
                    conversation_context["last_location"] = loc

    if "from" in words:
        idx = words.index("from")
        if idx + 1 < len(words):
            planning_state["source"] = normalize_location(words[idx + 1])

    for w in words:
        if w.isdigit():
            n = int(w)
            if n > 1000:
                planning_state["budget"] = n
            elif n < 20:
                planning_state["people"] = n


def infer_category_preference(text):
    """Infer a category preference for queries like 'falls in Goa'."""
    text = text.lower()
    if any(term in text for term in ["waterfall", "falls", "fall"]):
        return "waterfalls"
    if any(term in text for term in ["beach", "beaches"]):
        return "beaches"
    if any(term in text for term in ["temple", "church", "mosque", "religious"]):
        return "religion"
    if any(term in text for term in ["historic", "history", "fort", "palace", "museum"]):
        return "historic"
    if any(term in text for term in ["nature", "natural", "park"]):
        return "natural"
    return None


# ============================================================
# UNIFIED: Classify + Extract (LLM primary, keyword fallback)
# ============================================================
def classify_and_extract(user_input):
    """
    Main entry: tries LLM first, falls back to keywords.
    Updates planning_state and conversation_context.
    Returns the intent string.
    """
    # --- Try LLM first ---
    llm_result = llm_classify_and_extract(user_input)

    if llm_result and llm_result.get("intent"):
        intent = llm_result["intent"]

        # Update state from LLM extraction
        if llm_result.get("destination"):
            planning_state["destination"] = llm_result["destination"]
            conversation_context["last_location"] = llm_result["destination"]

        if llm_result.get("source"):
            planning_state["source"] = llm_result["source"]

        if llm_result.get("budget"):
            try:
                planning_state["budget"] = int(llm_result["budget"])
            except (ValueError, TypeError):
                pass

        if llm_result.get("people"):
            try:
                planning_state["people"] = int(llm_result["people"])
            except (ValueError, TypeError):
                pass
                
        if llm_result.get("transport_mode"):
            planning_state["transport_mode"] = str(llm_result["transport_mode"]).lower()
            
        if llm_result.get("category_preference"):
            planning_state["category_preference"] = str(llm_result["category_preference"]).lower()
        else:
            inferred_pref = infer_category_preference(user_input)
            if inferred_pref:
                planning_state["category_preference"] = inferred_pref
                llm_result["category_preference"] = inferred_pref
            
        if llm_result.get("days"):
            try:
                planning_state["days"] = int(str(llm_result["days"]).replace("days", "").strip())
            except ValueError:
                pass

        if llm_result.get("specific_places"):
            places = llm_result.get("specific_places")
            planning_state["specific_places"] = places if isinstance(places, list) else [places]

        # Track location from any query type
        if llm_result.get("location"):
            conversation_context["last_location"] = llm_result["location"]

        # Smart context fill: if planning but no destination, use last known location
        if intent == "planning" and not planning_state.get("destination"):
            if conversation_context.get("last_location"):
                planning_state["destination"] = conversation_context["last_location"]
                logger.info(f"[Context: using previously mentioned location → {planning_state['destination']}]")

        # Save to history
        conversation_context["history"].append({
            "query": user_input,
            "intent": intent,
            "llm_result": llm_result
        })

        return intent, llm_result

    # --- Fallback to keywords ---
    logger.warning("[Using keyword-based fallback]")
    keyword_extract_state(user_input)
    intent = keyword_classify_intent(user_input)

    # Context fill for planning
    if intent == "planning" and not planning_state.get("destination"):
        if conversation_context.get("last_location"):
            planning_state["destination"] = conversation_context["last_location"]
            logger.info(f"[Context: using previously mentioned location → {planning_state['destination']}]")

    fallback_result = {
        "intent": intent,
        "destination": planning_state.get("destination"),
        "source": planning_state.get("source"),
        "budget": planning_state.get("budget"),
        "people": planning_state.get("people"),
        "transport_mode": planning_state.get("transport_mode"),
        "category_preference": planning_state.get("category_preference"),
        "location": conversation_context.get("last_location")
    }

    conversation_context["history"].append({
        "query": user_input,
        "intent": intent,
        "llm_result": fallback_result
    })

    return intent, fallback_result


# ============================================================
# HELPER: Get location for current query
# ============================================================
def get_query_location(user_input):
    """
    Get the location relevant to the current query.
    Priority: LLM-extracted location > planning state > conversation context
    """
    # Check latest LLM result
    if conversation_context["history"]:
        last = conversation_context["history"][-1]
        if last.get("llm_result"):
            loc = last["llm_result"].get("location") or last["llm_result"].get("destination")
            if loc:
                return loc

    # Fallback to state
    if planning_state.get("destination"):
        return planning_state["destination"]

    # Fallback to last mentioned
    return conversation_context.get("last_location")


# ============================================================
# HELPER: Estimate trip days
# ============================================================
def estimate_days(budget, people):
    """Estimate reasonable trip duration based on budget."""
    if not budget:
        return 2

    per_person = budget / max(people or 1, 1)

    if per_person < 3000:
        return 1
    elif per_person < 7000:
        return 2
    elif per_person < 12000:
        return 3
    else:
        return 4


# ============================================================
# HANDLERS — Each intent has its own handler
# ============================================================

def handle_weather(user_input):
    """Handle weather queries."""
    location = get_query_location(user_input)

    if not location:
        return "🌤️ Please specify a location. Example: 'Weather in Goa'"

    result = safe_call(
        tool_fn=weather_tool,
        tool_name="weather",
        fallback_fn=lambda: get_weather_fallback(location),
        location=location
    )

    if not result["success"]:
        return f"❌ Couldn't fetch weather: {result['error']}"

    data = result["data"]
    source_tag = " (estimated)" if result["source"] == "fallback" else ""

    return (
        f"🌤️ Weather in {location}{source_tag}:\n"
        f"  🌡️  Temperature: {data.get('temperature', 'N/A')}°C\n"
        f"  ☁️  Condition: {data.get('description', 'N/A')}\n"
        f"  💧 Humidity: {data.get('humidity', 'N/A')}%"
    )


def handle_tourist(user_input):
    """Handle tourist attraction queries."""
    last = conversation_context["history"][-1]
    llm_result = last.get("llm_result") or {}

    location = llm_result.get("location") or llm_result.get("destination")
    if not location:
        location = get_query_location(user_input)
        
    category_preference = llm_result.get("category_preference") or infer_category_preference(user_input)

    if not location:
        return "🏛️ Please specify a location. Example: 'Places to visit in Wayanad'"

    result = safe_call(
        tool_fn=attraction_tool,
        tool_name="attraction",
        fallback_fn=lambda: {"location": location, "attractions": get_attraction_fallback(location)},
        location=location,
        category_preference=category_preference
    )

    if not result["success"]:
        return f"❌ Couldn't fetch attractions: {result['error']}"

    data = result["data"]
    attractions = data.get("attractions", [])
    source_tag = " (from local database)" if result["source"] == "fallback" else ""

    lines = [f"🏛️ Top places in {location}{source_tag}:\n"]
    for i, place in enumerate(attractions, 1):
        if isinstance(place, dict):
            name = place.get("name", "Unknown")
            cat = place.get("category", "")
            lines.append(f"  {i}. {name} [{cat}]")
        else:
            lines.append(f"  {i}. {place}")

    return "\n".join(lines)


def handle_restaurant(user_input):
    """Handle restaurant queries."""
    location = get_query_location(user_input)

    if not location:
        return "🍽️ Please specify a location. Example: 'Restaurants in Mumbai'"

    result = safe_call(
        tool_fn=restaurant_tool,
        tool_name="restaurant",
        fallback_fn=lambda: {"location": location, "restaurants": get_restaurant_fallback(location)},
        location=location
    )

    if not result["success"]:
        return f"❌ Couldn't fetch restaurants: {result['error']}"

    data = result["data"]
    restaurants = data.get("restaurants", [])
    source_tag = " (from local database)" if result["source"] == "fallback" else ""

    lines = [f"🍽️ Restaurants in {location}{source_tag}:\n"]
    for i, r in enumerate(restaurants, 1):
        if isinstance(r, dict):
            lines.append(f"  {i}. {r.get('name', 'Unknown')} — {r.get('cuisine', 'local')}")
        else:
            lines.append(f"  {i}. {r}")

    return "\n".join(lines)


def handle_hotel(user_input):
    """Handle hotel queries."""
    location = get_query_location(user_input)

    if not location:
        return "🏨 Please specify a location. Example: 'Hotels in Goa'"

    budget_str = str(planning_state.get("budget", "medium"))

    result = safe_call(
        tool_fn=hotel_tool,
        tool_name="hotel",
        fallback_fn=lambda: {"location": location, "budget": budget_str, "hotels": get_hotel_fallback(location)},
        location=location,
        budget=budget_str
    )

    if not result["success"]:
        return f"❌ Couldn't fetch hotels: {result['error']}"

    data = result["data"]
    hotels = data.get("hotels", [])
    source_tag = " (from local database)" if result["source"] == "fallback" else ""

    lines = [f"🏨 Hotels in {location}{source_tag}:\n"]
    for i, h in enumerate(hotels, 1):
        if isinstance(h, dict):
            name = h.get("name", "Unknown")
            price = h.get("price", "N/A")
            lines.append(f"  {i}. {name} — {price}")
        else:
            lines.append(f"  {i}. {h}")

    return "\n".join(lines)


def handle_distance(user_input):
    """Handle distance queries natively parsing LLM output, with keyword fallback."""
    last = conversation_context["history"][-1]
    llm_result = last.get("llm_result") or {}
    
    origin = llm_result.get("source")
    destination = llm_result.get("destination") or llm_result.get("location")

    # If the LLM failed to segregate source/destination, employ fallback parsing
    if not origin or not destination:
        if "to " in user_input.lower():
            parts = user_input.lower().split("to ")
            origin = parts[0].strip()
            destination = parts[1].strip()
        elif "and " in user_input.lower():
            parts = user_input.lower().split("and ")
            origin = parts[0].strip()
            destination = parts[1].strip()
        else:
            return "📏 Please specify both places. Example: 'Distance from Chennai to Goa'"

        # Clean up general prefix words
        for prefix in ["distance from ", "how far from ", "distance between "]:
            if origin.startswith(prefix):
                origin = origin.replace(prefix, "").strip()

        origin = normalize_location(origin)
        destination = normalize_location(destination)

    result = safe_call(
        tool_fn=distance_tool,
        tool_name="distance",
        origin=origin,
        destination=destination
    )

    if not result["success"]:
        return f"❌ Couldn't calculate distance: {result['error']}"

    data = result["data"]
    note = f"\n  ℹ️  {data.get('note', '')}" if data.get("note") else ""

    return (
        f"📏 Distance: {data.get('origin')} → {data.get('destination')}\n"
        f"  🛣️  {data.get('distance_km', 'N/A')} km\n"
        f"  ⏱️  ~{data.get('duration_hours', 'N/A')} hours{note}"
    )


def handle_budget(user_input):
    """Handle budget estimation queries."""
    dest = planning_state.get("destination")
    source = planning_state.get("source")

    if not dest:
        return "💰 Please tell me your destination first. Example: 'Plan a trip to Goa'"

    days = estimate_days(planning_state.get("budget"), planning_state.get("people"))
    people = planning_state.get("people") or 1

    # Get distance for cost estimation
    distance_km = 500  # default
    if source:
        dist_result = safe_call(
            tool_fn=distance_tool,
            tool_name="distance",
            origin=source,
            destination=dest
        )
        if dist_result["success"]:
            distance_km = dist_result["data"].get("distance_km", 500)

    # Determine budget type from total budget
    budget_total = planning_state.get("budget")
    if budget_total:
        per_person = budget_total / people
        if per_person < 5000:
            budget_type = "low"
        elif per_person < 15000:
            budget_type = "medium"
        else:
            budget_type = "high"
    else:
        budget_type = "medium"

    result = safe_call(
        tool_fn=estimate_budget,
        tool_name="budget",
        days=days,
        distance_km=distance_km,
        people=people,
        budget_type=budget_type
    )

    if not result["success"]:
        return f"❌ Couldn't estimate budget: {result['error']}"

    data = result["data"]

    return (
        f"💰 Budget Estimate for {dest} ({days} days, {people} people):\n\n"
        f"  🚗 Travel: ₹{data.get('travel_cost', 'N/A')}\n"
        f"  🍽️  Food:   ₹{data.get('food_cost', 'N/A')}\n"
        f"  🏨 Stay:   ₹{data.get('stay_cost', 'N/A')}\n"
        f"  ━━━━━━━━━━━━━━━━━━━━━\n"
        f"  💵 Total:  ₹{data.get('total_cost', 'N/A')}\n"
        f"  📊 Type:   {budget_type.upper()}"
    )


def handle_transport(user_input):
    """Handle transport queries."""
    from server.tools.transport import transport_tool
    
    # Try to extract source/destination
    last = conversation_context["history"][-1]
    llm_result = last.get("llm_result") or {}
    
    origin = llm_result.get("source")
    destination = llm_result.get("destination") or llm_result.get("location")

    if not origin or not destination:
        if "to " in user_input.lower():
            parts = user_input.lower().split("to ")
            origin = parts[0].strip().split()[-1]
            destination = parts[1].strip().split()[0]
        else:
            return "🚆 Please specify both places. Example: 'Transport from Chennai to Goa'"

    result = safe_call(
        tool_fn=transport_tool,
        tool_name="transport",
        origin=origin,
        destination=destination
    )

    if not result["success"]:
        return f"❌ Couldn't calculate transport: {result['error']}"

    data = result["data"]
    options = data.get("options", [])
    
    if not options:
        return f"🚆 No transport options found between {origin} and {destination}."
        
    lines = [f"🚆 Transport estimates: {data.get('origin')} → {data.get('destination')}\n"]
    for opt in options:
        mode = opt.get("mode", "").title()
        cost = opt.get("cost_per_person", "N/A")
        hrs = opt.get("duration_hours", "N/A")
        lines.append(f"  • {mode}: ₹{cost} per person (~{hrs} hours)")
        
    lines.append("\n⚠️ Note: These are rough estimates. Please verify real-time schedules and natively book via official sources like IRCTC, RedBus, or MakeMyTrip.")
    return "\n".join(lines)


def handle_currency(user_input):
    """Handle currency conversion queries."""
    from server.tools.currency import convert_currency
    import re
    
    # Simple regex extraction for amount
    amounts = re.findall(r'\b\d+(?:\.\d+)?\b', user_input)
    amount = float(amounts[0]) if amounts else 1.0
    
    # Determine currencies (simple fallback logic)
    text = user_input.lower()
    from_curr = "INR"
    to_curr = "USD"
    
    if "usd" in text or "dollars" in text:
        if "to inr" in text or "in inr" in text or "rupees" in text:
            from_curr, to_curr = "USD", "INR"
            
    if "eur" in text or "euro" in text:
        to_curr = "EUR"
        if "to inr" in text:
            from_curr, to_curr = "EUR", "INR"

    result = safe_call(
        tool_fn=convert_currency,
        tool_name="currency",
        amount=amount,
        from_currency=from_curr,
        to_currency=to_curr
    )

    if not result["success"]:
        return f"❌ Couldn't convert currency: {result['error']}"

    data = result["data"]
    return (
        f"💱 Currency Conversion:\n"
        f"  {data.get('original_amount')} {data.get('from_currency')} = {data.get('converted_amount')} {data.get('to_currency')}\n"
        f"  (Rate: 1 {data.get('from_currency')} = {data.get('conversion_rate')} {data.get('to_currency')})"
    )


# ============================================================
# MASTER PLANNER
# ============================================================


def plan_trip():
    supervisor = SupervisorAgent(safe_llm)
    
    # supervisor.plan_trip will handle everything and reset state
    final_response = supervisor.plan_trip(planning_state, estimate_days)
    
    planning_state.update({
        'destination': None,
        'source': None,
        'budget': None,
        'people': None,
        'transport_mode': None,
        'category_preference': None,
        'days': None
    })
    
    return final_response

# ============================================================
# HANDLER REGISTRY
# ============================================================
HANDLERS = {
    "weather": handle_weather,
    "tourist": handle_tourist,
    "restaurant": handle_restaurant,
    "hotel": handle_hotel,
    "distance": handle_distance,
    "transport": handle_transport,
    "currency": handle_currency,
    "budget": handle_budget,
    "planning": lambda _: plan_trip()
}

# ============================================================
# MAIN CHAT FUNCTION
# ============================================================

def chat(user_input):
    """Main entry point — route user input using the Handler Registry."""

    # LLM classifies intent + extracts entities in ONE call
    # Falls back to keyword-based if LLM fails
    intent, llm_result = classify_and_extract(user_input)

    logger.info(f"\n[Intent: {intent}] [State: src={planning_state.get('source')}, dst={planning_state.get('destination')}, "
          f"budget={planning_state.get('budget')}, people={planning_state.get('people')}]")

    # Gracefully reject non-travel queries
    if intent == "off_topic":
        return (
            "I am your Smart Travel Planner and I specialize in travel-related assistance only. "
            "I can help you with:\n"
            "  - Planning trips and itineraries\n"
            "  - Weather at destinations\n"
            "  - Tourist attractions, hotels, and restaurants\n"
            "  - Transport options and budget estimates\n"
            "  - Distances between cities\n\n"
            "Please ask me a travel-related question and I will be happy to help!"
        )

    if intent == "casual":
        return "You're welcome! Have a great trip! If you need help planning, just ask."

    # Route using Registry 
    handler = HANDLERS.get(intent)
    if handler:
        return handler(user_input)

    # ---- General fallback: travel-scoped LLM + RAG ----
    rag_result = query_knowledge(user_input, n_results=2)
    rag_context = ""
    if rag_result.get("success"):
        rag_context = f"\n\nRelevant Knowledge Base Context:\n{rag_result['context']}"
        logger.info({
            "event": "rag_hit",
            "query": user_input,
            "context_length": len(rag_result['context'])
        })
    else:
        logger.info({
            "event": "rag_miss",
            "query": user_input,
            "error": rag_result.get('error')
        })

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Smart Travel Planner assistant. "
                "You ONLY answer questions related to travel, tourism, geography, destinations, "
                "transport, visas, local culture, and travel tips.\n"
                "If the question is NOT related to travel, respond with exactly: "
                "'I am a travel assistant and can only help with travel-related questions. "
                "Try asking about destinations, weather, hotels, or trip planning!'\n"
                "For travel questions: be helpful, factual, and concise. "
                "Do NOT make up specific prices, timings, or place names."
                f"{rag_context}"
            )
        },
        {"role": "user", "content": user_input}
    ]

    try:
        reply = safe_llm(messages).choices[0].message.content
        # Strip any markdown that slips through
        return reply.replace("*", "").replace("#", "")
    except Exception as e:
        return f"Sorry, something went wrong: {str(e)}"



# ============================================================
# CLI ENTRY POINT
# ============================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  🧭 Smart Travel Planner — MCP Agent")
    print("  Type your travel query (or 'quit' to exit)")
    print("=" * 55)

    while True:
        try:
            q = input("\n🧑 You: ").strip()
            if q.lower() in ["quit", "exit", "q"]:
                logger.info("CLI session ended by user.")
                print("\n👋 Goodbye! Safe travels!")
                break
            if not q:
                continue
            print("\n🤖 AI:", chat(q))
        except KeyboardInterrupt:
            logger.info("CLI session interrupted by user.")
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error({"event": "cli_error", "error": str(e)})
            print(f"\n❌ Error: {e}")