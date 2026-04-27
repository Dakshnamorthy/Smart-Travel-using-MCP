"""
Summary Tool
=============
Generates a clean, user-friendly trip summary using LLM.
Takes tool-sourced data only.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def generate_trip_summary(city, days, itinerary, budget_info=None, distance_info=None, attractions=None):
    """
    Generate a clean trip summary from structured data.

    Args:
        city:          Destination city
        days:          Number of days
        itinerary:     The generated itinerary text
        budget_info:   Budget breakdown dict (optional)
        distance_info: Distance dict (optional)
        attractions:   List of attraction names or dicts (optional)
    """

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Normalize attractions
        attraction_names = []
        if attractions:
            for a in attractions:
                if isinstance(a, dict):
                    attraction_names.append(a.get("name", str(a)))
                else:
                    attraction_names.append(str(a))

        budget_text = ""
        if budget_info and isinstance(budget_info, dict):
            budget_text = f"""
        Budget Details:
        - Travel Cost: ₹{budget_info.get('travel_cost', 'N/A')}
        - Food Cost: ₹{budget_info.get('food_cost', 'N/A')}
        - Stay Cost: ₹{budget_info.get('stay_cost', 'N/A')}
        - Total Cost: ₹{budget_info.get('total_cost', 'N/A')}
        """

        distance_text = ""
        if distance_info and isinstance(distance_info, dict):
            distance_text = f"Distance: {distance_info.get('distance_km', 'N/A')} km"

        prompt = f"""
        Create a clean and engaging travel summary.

        City: {city}
        Days: {days}
        {distance_text}
        {budget_text}

        Attractions: {attraction_names}

        Itinerary:
        {itinerary}

        Instructions:
        - Make it user-friendly with emojis and headings
        - Include key highlights
        - Keep it concise (under 300 words)
        - Use ONLY the data provided
        """

        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": "You are a travel assistant. Summarize trips using ONLY provided data. Never hallucinate."},
                {"role": "user", "content": prompt}
            ]
        )

        summary = response.choices[0].message.content

        return {
            "city": city,
            "summary": summary
        }

    except Exception as e:
        return {"error": str(e)}