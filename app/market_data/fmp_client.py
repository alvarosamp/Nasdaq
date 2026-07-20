"""Thin client for Financial Modeling Prep's economic calendar.

Finnhub's free tier does not reliably expose macro/economic calendar data,
so this covers that gap. Free tier account required at
https://financialmodelingprep.com (separate API key from Finnhub).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://financialmodelingprep.com/api/v3/economic_calendar"


@dataclass
class EconomicEventEntry:
    event_name: str
    country: str
    event_date: datetime
    impact: str
    actual: str
    forecast: str
    previous: str


def get_economic_calendar(from_date: date, to_date: date) -> list[EconomicEventEntry]:
    if not settings.fmp_api_key:
        logger.warning("FMP_API_KEY não configurada — calendário econômico desativado.")
        return []

    try:
        resp = httpx.get(
            BASE_URL,
            params={
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "apikey": settings.fmp_api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.exception("Falha ao buscar calendário econômico na FMP")
        return []

    entries = []
    for item in data or []:
        raw_date = item.get("date")
        name = item.get("event")
        if not raw_date or not name:
            continue
        try:
            event_date = datetime.fromisoformat(raw_date).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        entries.append(
            EconomicEventEntry(
                event_name=name,
                country=item.get("country", ""),
                event_date=event_date,
                impact=(item.get("impact") or "low").lower(),
                actual=str(item.get("actual", "") or ""),
                forecast=str(item.get("estimate", "") or ""),
                previous=str(item.get("previous", "") or ""),
            )
        )
    return entries
