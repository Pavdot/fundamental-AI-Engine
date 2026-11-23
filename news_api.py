import os

import requests


class NewsFetchError(RuntimeError):
    pass


def fetch_news():
    token = os.getenv("FINNHUB_API_KEY")
    if not token:
        raise NewsFetchError("FINNHUB_API_KEY is required")

    try:
        response = requests.get(
            "https://finnhub.io/api/v1/news",
            params={"category": "general", "token": token},
            timeout=15,
        )
        response.raise_for_status()
        articles = response.json()
    except requests.RequestException:
        raise NewsFetchError("Finnhub request failed or returned invalid JSON") from None

    if not isinstance(articles, list):
        raise NewsFetchError("Finnhub did not return a list of articles")
    return articles
