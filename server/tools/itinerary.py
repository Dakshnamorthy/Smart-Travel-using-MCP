"""
Itinerary Tool
==============
Generates a structured day-wise itinerary using LLM.
Takes tool-sourced data only — never generates from scratch.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def generate_itinerary(city, days, attractions, restaurants, hotels=None, transport=None):
    """
    Generate a day-wise itinerary from structured data.

    Args:
        city:         Destination city name
        days:         Number of days
        attractions:  List of attraction names (strings) or dicts with 'name' key
        restaurants:  List of restaurant names (strings) or dicts with 'name' key
        hotels:       List of hotel info (optional)
        transport:    Transport options (optional)
    """

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Normalize: accept both strings and dicts
        attraction_names = []
        for a in attractions:
            if isinstance(a, dict):
                attraction_names.append(a.get("name", str(a)))
            else:
                attraction_names.append(str(a))

        restaurant_names = []
        for r in restaurants:
            if isinstance(r, dict):
                restaurant_names.append(r.get("name", str(r)))
            else:
                restaurant_names.append(str(r))

        hotel_info = ""
        if hotels:
            hotel_names = []
            for h in hotels:
                if isinstance(h, dict):
                    hotel_names.append(f"{h.get('name', 'Hotel')} ({h.get('price', 'N/A')})")
                else:
                    hotel_names.append(str(h))
            hotel_info = f"\nHotels: {hotel_names}"

        transport_info = ""
        if transport and isinstance(transport, dict):
            options = transport.get("options", [])
            if options:
                transport_info = f"\nTransport Options: {options}"

        prompt = f"""
        Plan a {days}-day trip in {city}.

        Attractions: {attraction_names}
        Restaurants: {restaurant_names}
        {hotel_info}
        {transport_info}

        Instructions:
        - Create a day-wise itinerary with morning/afternoon/evening slots
        - Use ONLY the places listed above — do NOT add any new places
        - Balance sightseeing and food
        - Keep it realistic and enjoyable
        - Add estimated time at each place
        """

        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": "You are a smart travel planner. Use ONLY the data provided. Do NOT hallucinate or add places not in the list."},
                {"role": "user", "content": prompt}
            ]
        )

        itinerary = response.choices[0].message.content

        return {
            "city": city,
            "days": days,
            "itinerary": itinerary
        }

    except Exception as e:
        return {"error": str(e)}