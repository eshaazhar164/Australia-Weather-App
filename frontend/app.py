import os
import requests

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify
)

app = Flask(__name__)
app.secret_key = "australia-weather-app"

BACKEND_URL = os.environ.get(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
)

CITIES = [
    "Sydney",
    "Melbourne",
    "Brisbane",
    "Perth",
    "Adelaide",
    "Canberra",
    "Hobart"
]


@app.route("/")
def home():
    selected_city = request.args.get("city", "All")

    if selected_city not in CITIES and selected_city != "All":
        selected_city = "All"

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/dashboard",
            params={"city": selected_city},
            timeout=60
        )
        response.raise_for_status()
        dashboard_data = response.json()

    except requests.exceptions.RequestException as error:
        print("Backend connection error:", error)
        flash(
            "Unable to connect to the backend. "
            "Please check that the backend service is running."
        )
        dashboard_data = {}

    return render_template(
        "index.html",
        weather_data=dashboard_data.get("weather_data", []),
        temperature_chart=dashboard_data.get("temperature_chart"),
        humidity_chart=dashboard_data.get("humidity_chart"),
        uv_chart=dashboard_data.get("uv_chart"),
        selected_city=dashboard_data.get(
            "selected_city", selected_city
        ),
        cities=dashboard_data.get("cities", CITIES),
        total_cities=dashboard_data.get("total_cities", 0),
        average_temperature=dashboard_data.get("average_temperature"),
        highest_temperature=dashboard_data.get("highest_temperature"),
        average_humidity=dashboard_data.get("average_humidity")
    )


@app.route("/refresh", methods=["GET", "POST"])
def refresh_weather():
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/refresh",
            timeout=120
        )
        response.raise_for_status()
        result = response.json()

        flash(
            result.get(
                "message",
                "Weather data refreshed successfully."
            )
        )

    except requests.exceptions.RequestException as error:
        print("Weather refresh error:", error)
        message = "Unable to refresh weather data."

        try:
            message = error.response.json().get("error", message)
        except (AttributeError, ValueError):
            pass

        flash(message)

    return redirect(url_for("home"))


# Gemini Chatbot Frontend Route
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json=data,
            timeout=90
        )

        result = response.json()

        return jsonify(result), response.status_code

    except requests.exceptions.RequestException as error:
        print("Chatbot connection error:", error)

        return jsonify({
            "error": "Unable to connect to the chatbot. Please try again."
        }), 503

    except ValueError:
        return jsonify({
            "error": "Invalid response received from the chatbot."
        }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
