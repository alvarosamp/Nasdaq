from dataclasses import dataclass

from app.dedup import filter_new_by_key
from app.market_data.finnhub_client import estimate_news_impact


@dataclass
class FakeArticle:
    url: str
    headline: str


def test_filter_new_by_key_skips_existing():
    articles = [FakeArticle("http://a", "A"), FakeArticle("http://b", "B")]
    existing = {"http://a"}
    result = filter_new_by_key(articles, existing, key_fn=lambda a: a.url)
    assert [a.url for a in result] == ["http://b"]


def test_filter_new_by_key_returns_all_when_no_overlap():
    articles = [FakeArticle("http://a", "A"), FakeArticle("http://b", "B")]
    result = filter_new_by_key(articles, set(), key_fn=lambda a: a.url)
    assert len(result) == 2


def test_filter_new_by_key_dedups_within_batch_itself():
    # two articles sharing the same url in the same batch should only keep the first
    articles = [FakeArticle("http://a", "first"), FakeArticle("http://a", "duplicate")]
    result = filter_new_by_key(articles, set(), key_fn=lambda a: a.url)
    assert len(result) == 1
    assert result[0].headline == "first"


def test_filter_new_by_key_empty_input():
    assert filter_new_by_key([], {"http://a"}, key_fn=lambda a: a.url) == []


def test_filter_new_by_key_tuple_keys_for_events():
    events = [("CPI", "US", "2026-01-01"), ("CPI", "US", "2026-02-01")]
    existing = {("CPI", "US", "2026-01-01")}
    result = filter_new_by_key(events, existing, key_fn=lambda e: e)
    assert result == [("CPI", "US", "2026-02-01")]


def test_estimate_news_impact_prioritizes_macro_terms():
    high = estimate_news_impact("Fed warns inflation and rates may stay high", "")
    low = estimate_news_impact("Company opens a small new office", "")
    assert high > low
    assert high >= 40
