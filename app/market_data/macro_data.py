"""Unified macro-instrument registry for the regime engine.

Routes each tracked instrument to whichever source is actually the primary
publisher of that data: Treasury yields and the dollar index come from
FRED (official, St. Louis Fed); index/commodity/FX futures stay on
yfinance, which has no better free alternative for those. See the
architecture notes in app/regime_engine.py for why this distinction
matters (Tier S vs Tier B data sources).

app.regime_engine and app.routers.regime should import MACRO_INSTRUMENTS,
get_macro_quote and get_macro_history from here, not from yfinance_client.
"""
from __future__ import annotations

import pandas as pd

from app.market_data import fred_client, yfinance_client

# key -> (source, symbol_or_series_id, display_name)
MACRO_INSTRUMENTS: dict[str, tuple[str, str, str]] = {
    "NASDAQ": ("yfinance", yfinance_client.NASDAQ_FUTURES_SYMBOL, "Nasdaq-100 (futuro)"),
    "SP500": ("yfinance", yfinance_client.SP500_FUTURES_SYMBOL, "S&P500 (futuro)"),
    "GOLD": ("yfinance", "GC=F", "Ouro"),
    # Trade-weighted dollar index (broad, goods & services) — FRED's official
    # replacement for the Yahoo DX-Y.NYB proxy.
    "DXY": ("fred", "DTWEXBGS", "Dollar Index (trade-weighted, Fed)"),
    "US2Y": ("fred", "DGS2", "Treasury 2 anos (yield)"),
    "US5Y": ("fred", "DGS5", "Treasury 5 anos (yield)"),
    "US10Y": ("fred", "DGS10", "Treasury 10 anos (yield)"),
    "US30Y": ("fred", "DGS30", "Treasury 30 anos (yield)"),
    "VIX": ("fred", "VIXCLS", "VIX (CBOE, via FRED)"),
    "BRENT": ("yfinance", "BZ=F", "Petroleo Brent"),
    "WTI": ("yfinance", "CL=F", "Petroleo WTI"),
    "EURUSD": ("yfinance", "EURUSD=X", "EUR/USD"),
    "EURBRL": ("yfinance", "EURBRL=X", "EUR/BRL"),
}


def get_macro_quote(key: str):
    """Latest quote for one MACRO_INSTRUMENTS entry. Returns an object with
    .symbol/.name/.price/.change_pct/.updated_at regardless of source
    (yfinance_client.IndexQuote or fred_client.FredQuote) — callers
    (regime_engine.store_macro_snapshots) only read those common fields.
    """
    entry = MACRO_INSTRUMENTS.get(key.upper())
    if entry is None:
        return None
    source, symbol, name = entry
    if source == "fred":
        quote = fred_client.get_quote(symbol, name)
        if quote is None:
            return None
        return yfinance_client.IndexQuote(
            symbol=symbol,
            name=name,
            price=quote.value,
            change_pct=quote.change_pct,
            day_high=quote.value,
            day_low=quote.value,
            prev_close=quote.value,
            updated_at=quote.updated_at,
        )
    return yfinance_client.get_index_quote(symbol, name)


def get_macro_history(key: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Daily history for a MACRO_INSTRUMENTS entry — used for rolling
    correlation/regime calculations, which need a return series rather than
    just the latest quote.
    """
    entry = MACRO_INSTRUMENTS.get(key.upper())
    if entry is None:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    source, symbol, _name = entry
    if source == "fred":
        return fred_client.get_series(symbol)
    return yfinance_client.get_history(symbol, period=period, interval=interval)
