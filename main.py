from flask import Flask, render_template, redirect, url_for, flash, request
import firebase_admin
from firebase_admin import credentials, db
from pathlib import Path

from backend.weather_service import get_all_weather
from backend.charts import (
    create_temperature_chart,
    create_humidity_chart,
    create_uv_chart
)

# Project paths
BASE_DIR = Path(__file__).resolve().parent
KEY_PATH = BASE_DIR / "serviceAccountKey.json"

# Flask application
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "frontend" / "templates"),
    static_folder=str(BASE_DIR / "frontend" / "static")
)

app.secret_key = "australia-weather-app"

# Firebase configuration
DATABASE_URL = (
    "https://australia-weather-app-default-rtdb.firebaseio.com/"
)

firebase_error = None

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(str(KEY_PATH))
        firebase_admin.initialize_app(
            cred,
            {"databaseURL": DATABASE_URL}
        )

    print("Firebase initialized successfully.")

except Exception as error:
    firebase_error = error
    print("Firebase initialization error:", error)


# Australian cities
CITIES = [
    "Sydney",
    "Melbourne",
    "Brisbane",
    "Perth",
    "Adelaide",
    "Canberra",
    "Hobart"
]


# Main dashboard
@app.route("/")
def home():
    weather_data = []

    if firebase_error is None:
        try:
            data = db.reference("weather").get() or {}

            if isinstance(data, dict):
                weather_data = [
                    item
                    for item in data.values()
                    if isinstance(item, dict)
                ]

        except Exception as error:
            print("Firebase read error:", error)
            flash(
                "Unable to load weather data from Firebase. "
                "Please check your connection and try again."
            )
    else:
        flash(
            "Firebase is not initialized. "
            "Please check your Firebase configuration."
        )

    # Filter weather records by city
    selected_city = request.args.get("city", "All")

    if selected_city not in CITIES and selected_city != "All":
        selected_city = "All"

    if selected_city != "All":
        weather_data = [
            item for item in weather_data
            if item.get("city") == selected_city
        ]

    # Calculate summary statistics
    temperatures = []
    humidity_values = []

    for item in weather_data:
        try:
            value = item.get("current_temperature")
            if value is not None:
                temperatures.append(float(value))
        except (TypeError, ValueError):
            print("Invalid temperature value:", item.get("city"))

        try:
            value = item.get("humidity")
            if value is not None:
                humidity_values.append(float(value))
        except (TypeError, ValueError):
            print("Invalid humidity value:", item.get("city"))

    total_cities = len(weather_data)

    average_temperature = (
        round(sum(temperatures) / len(temperatures), 1)
        if temperatures else None
    )

    highest_temperature = (
        max(temperatures) if temperatures else None
    )

    average_humidity = (
        round(sum(humidity_values) / len(humidity_values), 1)
        if humidity_values else None
    )

    # Generate charts
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

        if not all([
            temperature_chart,
            humidity_chart,
            uv_chart
        ]):
            flash(
                "Some charts could not be generated. "
                "Please check the VS Code terminal."
            )

    return render_template(
        "index.html",
        weather_data=weather_data,
        temperature_chart=temperature_chart,
        humidity_chart=humidity_chart,
        uv_chart=uv_chart,
        selected_city=selected_city,
        cities=CITIES,
        total_cities=total_cities,
        average_temperature=average_temperature,
        highest_temperature=highest_temperature,
        average_humidity=average_humidity
    )


# Refresh weather data
@app.route("/refresh")
def refresh_weather():
    if firebase_error is not None:
        print("Firebase initialization failed:", firebase_error)
        flash(
            "Firebase is unavailable. "
            "Please check your Firebase configuration."
        )
        return redirect(url_for("home"))

    try:
        weather_data = get_all_weather()
    except Exception as error:
        print("Weather service error:", error)
        flash(
            "Unable to retrieve weather data. "
            "Please check your internet connection."
        )
        return redirect(url_for("home"))

    if not weather_data:
        flash(
            "No weather data was retrieved. "
            "Existing Firebase data has not been changed."
        )
        return redirect(url_for("home"))

    try:
        database_data = {
            item["city"]: item
            for item in weather_data
            if item.get("city") in CITIES
        }

        if not database_data:
            flash("No valid weather records were available to save.")
            return redirect(url_for("home"))

    except (KeyError, TypeError, AttributeError) as error:
        print("Weather data preparation error:", error)
        flash("Weather data could not be prepared for Firebase.")
        return redirect(url_for("home"))

    try:
        db.reference("weather").set(database_data)

        print(
            "Firebase updated successfully for",
            len(database_data),
            "cities."
        )

        flash(
            "Weather data saved successfully for "
            f"{len(database_data)} cities."
        )

    except Exception as error:
        print("Firebase write error:", error)
        flash(
            "Weather data was retrieved, but Firebase could not "
            "save it. Please check the connection and permissions."
        )

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
