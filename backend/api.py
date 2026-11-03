from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials, db
from pathlib import Path
import json

from weather_service import get_all_weather
from charts import (
    create_temperature_chart,
    create_humidity_chart,
    create_uv_chart
)
from chatbot import get_chatbot_response

app = Flask(__name__)

DATABASE_URL = (
    "https://australia-weather-app-default-rtdb.firebaseio.com/"
)

KEY_PATH = Path("/app/serviceAccountKey.json")

CITIES = [
    "Sydney",
    "Melbourne",
    "Brisbane",
    "Perth",
    "Adelaide",
    "Canberra",
    "Hobart"
]

firebase_error = None

try:
    if not firebase_admin._apps:
        if not KEY_PATH.exists():
            raise FileNotFoundError(
                "Firebase service account key is missing."
            )

        cred = credentials.Certificate(str(KEY_PATH))
        firebase_admin.initialize_app(
            cred,
            {"databaseURL": DATABASE_URL}
        )

    print("Firebase initialized successfully.")

except Exception as error:
    firebase_error = str(error)
    print("Firebase initialization error:", error)


@app.route("/api/health")
def health():
    return jsonify({"status": "running"})


@app.route("/api/dashboard")
def dashboard():
    if firebase_error:
        return jsonify({
            "error": "Firebase initialization failed."
        }), 503

    try:
        data = db.reference("weather").get() or {}

        weather_data = [
            item for item in data.values()
            if isinstance(item, dict)
        ] if isinstance(data, dict) else []

        selected_city = request.args.get("city", "All")

        if selected_city not in CITIES and selected_city != "All":
            selected_city = "All"

        if selected_city != "All":
            weather_data = [
                item for item in weather_data
                if item.get("city") == selected_city
            ]

        temperatures = []
        humidity_values = []

        for item in weather_data:
            try:
                value = item.get("current_temperature")
                if value is not None:
                    temperatures.append(float(value))
            except (TypeError, ValueError):
                pass

            try:
                value = item.get("humidity")
                if value is not None:
                    humidity_values.append(float(value))
            except (TypeError, ValueError):
                pass

        temperature_chart = None
        humidity_chart = None
        uv_chart = None

        if weather_data:
            try:
                temperature_chart = create_temperature_chart(
                    weather_data
                )
            except Exception as error:
                print("Temperature chart error:", error)

            try:
                humidity_chart = create_humidity_chart(
                    weather_data
                )
            except Exception as error:
                print("Humidity chart error:", error)

            try:
                uv_chart = create_uv_chart(weather_data)
            except Exception as error:
                print("UV chart error:", error)

        return jsonify({
            "weather_data": weather_data,
            "temperature_chart": temperature_chart,
            "humidity_chart": humidity_chart,
            "uv_chart": uv_chart,
            "selected_city": selected_city,
            "cities": CITIES,
            "total_cities": len(weather_data),
            "average_temperature": (
                round(sum(temperatures) / len(temperatures), 1)
                if temperatures else None
            ),
            "highest_temperature": (
                max(temperatures) if temperatures else None
            ),
            "average_humidity": (
                round(sum(humidity_values) / len(humidity_values), 1)
                if humidity_values else None
            )
        })

    except Exception as error:
        print("Dashboard API error:", error)
        return jsonify({
            "error": "Unable to load dashboard data."
        }), 500


@app.route("/api/refresh", methods=["POST"])
def refresh_weather():
    if firebase_error:
        return jsonify({
            "error": "Firebase is unavailable."
        }), 503

    try:
        weather_data = get_all_weather()

        if not weather_data:
            return jsonify({
                "error": "No weather data was retrieved."
            }), 502

        database_data = {
            item["city"]: item
            for item in weather_data
            if item.get("city") in CITIES
        }

        if not database_data:
            return jsonify({
                "error": "No valid weather records were found."
            }), 502

        db.reference("weather").set(database_data)

        return jsonify({
            "message": (
                f"Weather data saved for "
                f"{len(database_data)} cities."
            )
        })

    except Exception as error:
        print("Weather refresh error:", error)
        return jsonify({
            "error": "Weather data could not be refreshed."
        }), 500


# Gemini AI Chatbot API
@app.route("/api/chat", methods=["POST"])
def chat():
    if firebase_error:
        return jsonify({
            "error": "Weather database is currently unavailable."
        }), 503

    try:
        request_data = request.get_json(silent=True) or {}

        message = request_data.get("message", "")

        if not isinstance(message, str) or not message.strip():
            return jsonify({
                "error": "Please enter a message."
            }), 400

        if len(message) > 1000:
            return jsonify({
                "error": "Message must be under 1000 characters."
            }), 400

        history = request_data.get("history", [])

        if not isinstance(history, list):
            history = []

        history = [
            item for item in history[-10:]
            if isinstance(item, dict)
            and item.get("role") in ["user", "model"]
            and isinstance(item.get("content"), str)
        ]

        weather_data = db.reference("weather").get() or {}

        if isinstance(weather_data, dict):
            weather_records = [
                item for item in weather_data.values()
                if isinstance(item, dict)
            ]
        else:
            weather_records = []

        weather_context = json.dumps(
            weather_records,
            ensure_ascii=False,
            default=str
        )

        answer = get_chatbot_response(
            message=message.strip(),
            weather_context=weather_context,
            history=history
        )

        return jsonify({
            "response": answer
        })

    except Exception as error:
        print("Chatbot API error:", error)
        return jsonify({
            "error": "Chatbot is temporarily unavailable."
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False
    )
