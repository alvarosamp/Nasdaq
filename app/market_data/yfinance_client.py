"""Historical OHLCV data via yfinance (no API key required).

Used to build the price/volume history needed to compute technical
indicators (RSI, MACD, moving averages, volume averages). Finnhub's free
tier does not include historical candles for US equities, so this fills
that gap at no cost.
"""
from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


_COLUMNS = ["open", "high", "low", "close", "volume"]


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
