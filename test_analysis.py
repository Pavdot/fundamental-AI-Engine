from unittest.mock import Mock
import pytest
import main


def test_analyze_news_retries(monkeypatch):
    fake_llm = Mock(side_effect=[
        "INVALID JSON",
        '{"asset":"BTC","direction":-0.8,"importance":0.9,"confidence":0.85,"horizon_hours":24}'
    ])

    monkeypatch.setattr(main, "call_llm", fake_llm)

    result = main.analyze_news("Bitcoin falls")

    assert fake_llm.call_count == 2
    assert result.asset == "BTC"

def test_retry_then_success(monkeypatch):
    fake_llm = Mock(side_effect=[
        "INVALID JSON",
        '{"asset":"BTC","direction":-0.8,"importance":0.9,"confidence":0.85,"horizon_hours":24}'
    ])

    monkeypatch.setattr(main, "call_llm", fake_llm)

    result = main.analyze_news("Bitcoin falls")