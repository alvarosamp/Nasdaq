import numpy as np
import pandas as pd

from app import indicators


def _series(values):
    idx = pd.date_range("2024-01-01", periods=len(values), freq="min")
    return pd.Series(values, index=idx, dtype=float)


def test_sma_basic():
    s = _series([1, 2, 3, 4, 5])
    result = indicators.sma(s, period=3)
    assert np.isnan(result.iloc[0])
    assert result.iloc[2] == 2.0
    assert result.iloc[4] == 4.0


def test_ema_converges_towards_price_trend():
    s = _series([10] * 20 + [20] * 20)
    result = indicators.ema(s, period=5)
    # after the jump to 20, EMA should trend up and eventually get close to 20
    assert result.iloc[-1] > result.iloc[20]
    assert result.iloc[-1] < 20
    assert result.iloc[-1] > 18


def test_rsi_all_gains_is_100():
    s = _series(list(range(1, 30)))  # strictly increasing -> no losses
    result = indicators.rsi(s, period=14)
    assert result.iloc[-1] == 100.0


def test_rsi_all_losses_is_0():
    s = _series(list(range(30, 1, -1)))  # strictly decreasing -> no gains
    result = indicators.rsi(s, period=14)
    assert result.iloc[-1] == 0.0


def test_macd_columns_present():
    s = _series(np.sin(np.linspace(0, 10, 60)) * 5 + 100)
    result = indicators.macd(s)
    assert list(result.columns) == ["macd", "signal", "histogram"]
    assert not result["macd"].isna().all()


def test_bollinger_bands_ordering():
    s = _series(np.random.default_rng(0).normal(100, 2, 40))
    result = indicators.bollinger_bands(s, period=20)
    valid = result.dropna()
    assert (valid["upper"] >= valid["mid"]).all()
    assert (valid["mid"] >= valid["lower"]).all()


def test_volume_ratio_spike_detected():
    volumes = _series([100] * 20 + [1000])
    result = indicators.volume_ratio(volumes, period=20)
    assert result.iloc[-1] > 5


def test_pct_change_over_window():
    s = _series([100, 110])
    result = indicators.pct_change_over_window(s, periods=1)
    assert round(result.iloc[-1], 2) == 10.0
