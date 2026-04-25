from __future__ import annotations

import webbrowser
from urllib.parse import quote_plus

import requests

from jarvis.utils.config import settings


def open_website(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    webbrowser.open(url)
    return f"Opening {url}"


def google_search(query: str) -> str:
    webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
    return f"Searching Google for {query}."


def youtube_search(query: str) -> str:
    webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
    return f"Searching YouTube for {query}."


def get_weather(city: str | None = None) -> str:
    if not settings.weather_api_key:
        return "Weather API key missing. Set WEATHER_API_KEY in .env."
    target_city = (city or settings.weather_default_city).strip()
    if not target_city:
        return "Sure - which city should I check the weather for?"
    query = f"{target_city},{settings.weather_country_code}" if settings.weather_country_code else target_city
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": query, "appid": settings.weather_api_key, "units": "metric"}
    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.RequestException:
        return "Weather service is unreachable right now."
    if resp.status_code != 200:
        try:
            details = resp.json().get("message", "")
        except Exception:
            details = ""
        if "city not found" in details.lower():
            return f"I could not find weather for {target_city}. Which city should I try?"
        return f"Could not fetch weather right now ({resp.status_code})."
    payload = resp.json()
    temp = payload["main"]["temp"]
    feels = payload["main"].get("feels_like", temp)
    desc = payload["weather"][0]["description"]
    wind = payload.get("wind", {}).get("speed", 0)
    name = payload.get("name", target_city)
    return (
        f"{name}: {temp}C, feels like {feels}C, {desc}. "
        f"Wind speed is {wind} m/s."
    )


def get_news(country: str = "us") -> str:
    if not settings.news_api_key:
        return "News API key missing. Set NEWS_API_KEY in .env."
    url = "https://newsapi.org/v2/top-headlines"
    params = {"country": country, "apiKey": settings.news_api_key, "pageSize": 3}
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        return "Could not fetch news right now."
    articles = resp.json().get("articles", [])
    if not articles:
        return "No headlines found."
    lines = [f"{idx + 1}. {article['title']}" for idx, article in enumerate(articles)]
    return "Top headlines: " + " | ".join(lines)
