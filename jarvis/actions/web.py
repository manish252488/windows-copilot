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


def get_weather(city: str) -> str:
    if not settings.weather_api_key:
        return "Weather API key missing. Set WEATHER_API_KEY in .env."
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": settings.weather_api_key, "units": "metric"}
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        return "Could not fetch weather right now."
    payload = resp.json()
    temp = payload["main"]["temp"]
    desc = payload["weather"][0]["description"]
    return f"It is {temp} degrees Celsius in {city} with {desc}."


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
