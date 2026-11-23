from contextlib import closing
import json
import sqlite3
import time
from unittest.mock import Mock

import pytest
import requests

import alerts
from database import initialize
import main
import news_api


def article(article_id, headline, published=None):
    return {
        "id": article_id,
        "headline": headline,
        "datetime": int(time.time()) if published is None else published,
    }


def btc_analysis():
    return json.dumps({
        "asset": "BTCUSDT", "direction": 0.5, "importance": 0.8,
        "confidence": 0.9, "horizon_hours": 12,
    })


def test_failed_analysis_is_retried_and_success_survives_restart(tmp_path, monkeypatch):
    path = tmp_path / "news.db"
    monkeypatch.setattr(main, "fetch_news", lambda: [
        article(1, "Bitcoin demand rises"),
        article(2, "Unrelated earnings report"),
        article(3, "Gold demand rises", published=1),
    ])
    llm = Mock(side_effect=["invalid"] * 3 + [btc_analysis()])
    monkeypatch.setattr(main, "call_llm", llm)

    with closing(sqlite3.connect(path)) as connection:
        initialize(connection)
        assert main.run_once(connection) == 1
        assert connection.execute("SELECT count(*) FROM articles").fetchone() == (0,)

    with closing(sqlite3.connect(path)) as connection:
        initialize(connection)
        assert main.run_once(connection) == 0

    with closing(sqlite3.connect(path)) as connection:
        initialize(connection)
        assert main.run_once(connection) == 0
        assert connection.execute("SELECT source_article_id FROM articles").fetchall() == [(1,)]
        assert connection.execute("SELECT target_asset FROM analyses").fetchall() == [("BTCUSDT",)]
    assert llm.call_count == 4


def test_macro_news_can_produce_one_analysis_per_asset(monkeypatch):
    monkeypatch.setattr(main, "fetch_news", lambda: [article(1, "FOMC holds rates")])
    llm = Mock(side_effect=[btc_analysis(), btc_analysis().replace("BTCUSDT", "XAUUSD")])
    monkeypatch.setattr(main, "call_llm", llm)
    with closing(sqlite3.connect(":memory:")) as connection:
        initialize(connection)
        assert main.run_once(connection) == 0
        assert connection.execute(
            "SELECT target_asset FROM analyses ORDER BY target_asset"
        ).fetchall() == [("BTCUSDT",), ("XAUUSD",)]
        assert connection.execute("SELECT count(*) FROM articles").fetchone() == (1,)


@pytest.mark.parametrize("ambiguous", [False, True])
def test_telegram_does_not_resend_confirmed_or_ambiguous_alerts(monkeypatch, ambiguous):
    monkeypatch.setattr(main, "fetch_news", lambda: [article(1, "Bitcoin demand rises")])
    monkeypatch.setattr(main, "call_llm", lambda prompt: btc_analysis())
    response = Mock(ok=True)
    response.json.return_value = {"ok": True}
    post = Mock(return_value=response, side_effect=requests.Timeout() if ambiguous else None)
    monkeypatch.setattr(alerts.requests, "post", post)

    with closing(sqlite3.connect(":memory:")) as connection:
        initialize(connection)
        assert main.run_once(connection, telegram=("fake", "123")) == int(ambiguous)
        assert main.run_once(connection, telegram=("fake", "123")) == 0
        expected_status = "uncertain" if ambiguous else "sent"
        assert connection.execute("SELECT status FROM alerts").fetchone() == (expected_status,)
    assert post.call_count == 1


def test_finnhub_rejects_error_payload(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "fake")
    response = Mock()
    response.json.return_value = {"error": "limit reached"}
    monkeypatch.setattr(news_api.requests, "get", Mock(return_value=response))
    with pytest.raises(news_api.NewsFetchError, match="did not return a list"):
        news_api.fetch_news()
