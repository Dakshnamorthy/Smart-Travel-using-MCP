import os
import json
from datetime import datetime


def save_trip(city, itinerary, budget, summary):
    try:
        # -------------------------------
        # Step 1: Create folder
        # -------------------------------
        folder = "saved_trips"

        if not os.path.exists(folder):
            os.makedirs(folder)

        # -------------------------------
        # Step 2: Create file name
        # -------------------------------
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{city.lower().replace(' ', '_')}_{timestamp}.json"

        filepath = os.path.join(folder, filename)

        # -------------------------------
        # Step 3: Prepare data
        # -------------------------------
        trip_data = {
            "city": city,
            "timestamp": timestamp,
            "itinerary": itinerary,
            "budget": budget,
            "summary": summary
        }

        # -------------------------------
        # Step 4: Save file
        # -------------------------------
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trip_data, f, indent=4)

        return {
            "message": "Trip saved successfully",
            "file_path": filepath
        }

    except Exception as e:
        return {"error": str(e)}