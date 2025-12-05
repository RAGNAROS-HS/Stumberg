import requests
from langchain_core.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get current weather information for a location."""
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": location, "count": 1, "language": "en", "format": "json"}
    
    geo_resp = requests.get(geo_url, params=geo_params)
    geo_data = geo_resp.json()
    
    if not geo_data.get("results"):
        return f"Could not find weather data for {location}"
    
    result = geo_data["results"][0]
    lat, lon = result["latitude"], result["longitude"]
    
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": lat, "longitude": lon, "current_weather": "true",
        "timezone": "auto", "forecast_days": 1
    }
    
    weather_resp = requests.get(weather_url, params=weather_params)
    weather_data = weather_resp.json()
    current = weather_data["current_weather"]
    
    weather_codes = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                     45: "Fog", 61: "Slight rain", 63: "Moderate rain", 71: "Slight snow",
                     95: "Thunderstorm"}
    desc = weather_codes.get(current["weathercode"], "Unknown")
    
    return f"Weather in {location}: {desc}, {current['temperature']:.0f}°C"
