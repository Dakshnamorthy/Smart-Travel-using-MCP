import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("EXCHANGE_API_KEY")


def convert_currency(amount: float, from_currency: str, to_currency: str):
    try:
        # -------------------------------
        # Step 1: Call API
        # -------------------------------
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{from_currency.upper()}"

        response = requests.get(url)
        data = response.json()

        if data.get("result") != "success":
            return {"error": "API request failed"}

        rates = data.get("conversion_rates", {})

        if to_currency.upper() not in rates:
            return {"error": "Invalid target currency"}

        # -------------------------------
        # Step 2: Convert
        # -------------------------------
        rate = rates[to_currency.upper()]
        converted_amount = round(amount * rate, 2)

        return {
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "original_amount": amount,
            "conversion_rate": rate,
            "converted_amount": converted_amount
        }

    except Exception as e:
        return {"error": str(e)}