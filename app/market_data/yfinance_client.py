"""Historical OHLCV data via yfinance (no API key required).

Used to build the price/volume history needed to compute technical
indicators (RSI, MACD, moving averages, volume averages). Finnhub's free
tier does not include historical candles for US equities, so this fills
that gap at no cost.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


_COLUMNS = ["open", "high", "low", "close", "volume"]


@dataclass
class FxQuote:
    pair: str
    rate: float
    change_pct: float
    updated_at: datetime


@dataclass
class CommodityQuote:
    symbol: str
    name: str
    unit: str
    price: float
    change_pct: float
    updated_at: datetime


def get_history(symbol: str, period: str = "5d", interval: str = "15m") -> pd.DataFrame:
    """Returns a DataFrame with columns [open, high, low, close, volume], indexed by
    datetime (ascending). open/high/low are used for the candlestick chart; close/volume
    are what the indicators and rules engine consume.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)
    except Exception:
        logger.exception("Falha ao buscar histórico de %s no yfinance", symbol)
        return pd.DataFrame(columns=_COLUMNS)

    if df.empty:
        return pd.DataFrame(columns=_COLUMNS)

    out = df.rename(
        columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    )[_COLUMNS]
    out.index.name = "timestamp"
    return out


def get_usd_brl_quote() -> FxQuote | None:
    """Returns the USD/BRL exchange rate from Yahoo Finance's BRL=X ticker."""
    history = get_history("BRL=X", period="5d", interval="1d")
    if history.empty:
        return None

    close = history["close"].dropna()
    if close.empty:
        return None

    latest = float(close.iloc[-1])
    previous = float(close.iloc[-2]) if len(close) >= 2 else latest
    change_pct = ((latest - previous) / previous * 100) if previous else 0.0
    timestamp = close.index[-1]
    if hasattr(timestamp, "to_pydatetime"):
        updated_at = timestamp.to_pydatetime()
    else:
        updated_at = datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)

    return FxQuote(pair="USD/BRL", rate=latest, change_pct=change_pct, updated_at=updated_at)


def get_gold_quote() -> CommodityQuote | None:
    """Returns the gold futures price (GC=F), quoted in USD per troy ounce."""
    history = get_history("GC=F", period="5d", interval="1d")
    if history.empty:
        return None

    close = history["close"].dropna()
    if close.empty:
        return None

    latest = float(close.iloc[-1])
    previous = float(close.iloc[-2]) if len(close) >= 2 else latest
    change_pct = ((latest - previous) / previous * 100) if previous else 0.0
    timestamp = close.index[-1]
    if hasattr(timestamp, "to_pydatetime"):
        updated_at = timestamp.to_pydatetime()
    else:
        updated_at = datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)

    return CommodityQuote(
        symbol="GC=F",
        name="Ouro",
        unit="onca troy",
        price=latest,
        change_pct=change_pct,
        updated_at=updated_at,
    )
