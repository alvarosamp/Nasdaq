"""Pure pandas implementations of common technical indicators.

All functions take a pandas Series/DataFrame with a DatetimeIndex and return
a Series aligned to the same index, so no external TA dependency is needed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(close: pd.Series, period: int) -> pd.Series:
    return close.rolling(window=period, min_periods=period).mean()


def ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    result = 100 - (100 / (1 + rs))
    # avg_loss == 0 (no losses in window) -> RSI is 100; keep NaN where not enough data yet
    result = result.where(avg_loss != 0, 100.0)
    result[avg_gain.isna() | avg_loss.isna()] = np.nan
    return result


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "histogram": histogram})


def bollinger_bands(close: pd.Series, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    mid = sma(close, period)
    std = close.rolling(window=period, min_periods=period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return pd.DataFrame({"mid": mid, "upper": upper, "lower": lower})


def volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
    """Current volume / rolling average volume."""
    avg_vol = volume.rolling(window=period, min_periods=period).mean()
    return volume / avg_vol.replace(0, pd.NA)


def pct_change_over_window(close: pd.Series, periods: int = 1) -> pd.Series:
    return close.pct_change(periods=periods) * 100
