import requests

CITIES = {
    "Sydney": (-33.8688, 151.2093),
    "Melbourne": (-37.8136, 144.9631),
    "Brisbane": (-27.4698, 153.0251),
    "Perth": (-31.9505, 115.8605),
    "Adelaide": (-34.9285, 138.6007),
    "Canberra": (-35.2809, 149.1300),
    "Hobart": (-42.8821, 147.3272)
}

WEATHER_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Light Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Light Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    80: "Rain Showers",
    81: "Moderate Rain Showers",
    82: "Heavy Rain Showers",
    95: "Thunderstorm"
}


def get_weather(city, latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,"
            "apparent_temperature,is_day,weather_code,"
            "wind_speed_10m,uv_index"
        ),
        "daily": (
            "temperature_2m_max,temperature_2m_min,"
            "uv_index_max,sunshine_duration"
        ),
        "timezone": "auto",
        "forecast_days": 1
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    current = data["current"]
    daily = data["daily"]

    return {
        "country": "Australia",
        "city": city,
        "current_temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "minimum_temperature": daily["temperature_2m_min"][0],
        "maximum_temperature": daily["temperature_2m_max"][0],
        "weather_condition": WEATHER_CODES.get(
            current["weather_code"], "Other"
        ),
        "uv_index": current["uv_index"],
        "maximum_uv_index": daily["uv_index_max"][0],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "sunshine_hours": round(
            daily["sunshine_duration"][0] / 3600, 2
        ),
        "is_daytime": bool(current["is_day"]),
        "last_updated": current["time"]
    }


def get_all_weather():
    weather_data = []

    for city, coordinates in CITIES.items():
        try:
            result = get_weather(city, *coordinates)
            weather_data.append(result)

            print(f"Weather fetched successfully: {city}")

        except requests.exceptions.Timeout:
            print(f"Timeout error for {city}. Skipping this city.")

        except requests.exceptions.HTTPError as error:
            print(f"Weather API HTTP error for {city}: {error}")

        except requests.exceptions.RequestException as error:
            print(f"Weather API connection error for {city}: {error}")

        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError
        ) as error:
            print(f"Invalid weather data for {city}: {error}")

    if not weather_data:
        print("No weather data could be retrieved.")

    return weather_data
