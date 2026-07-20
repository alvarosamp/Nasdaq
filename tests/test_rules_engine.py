from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from app.models import RuleType
from app.rules_engine import MarketState, RuleContext, cooldown_expired, evaluate_rule


def _history(closes, volumes=None):
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="15min")
    volumes = volumes or [1000] * len(closes)
    return pd.DataFrame({"close": closes, "volume": volumes}, index=idx)


def _state(symbol="AAPL", price=None, change_pct=0.0, closes=None, volumes=None):
    closes = closes or [100.0] * 30
    price = price if price is not None else closes[-1]
    return MarketState(
        symbol=symbol,
        price=price,
        change_pct=change_pct,
        volume=volumes[-1] if volumes else 1000,
        history=_history(closes, volumes),
    )


def test_price_above_triggers():
    rule = RuleContext(RuleType.PRICE_ABOVE, threshold=150, param_a=0, param_b=0)
    state = _state(price=160)
    result = evaluate_rule(rule, state)
    assert result.triggered
    assert "AAPL" in result.message


def test_price_above_does_not_trigger_when_below():
    rule = RuleContext(RuleType.PRICE_ABOVE, threshold=150, param_a=0, param_b=0)
    state = _state(price=140)
    assert not evaluate_rule(rule, state).triggered


def test_price_below_triggers():
    rule = RuleContext(RuleType.PRICE_BELOW, threshold=150, param_a=0, param_b=0)
    state = _state(price=140)
    assert evaluate_rule(rule, state).triggered


def test_pct_change_triggers_on_large_move():
    rule = RuleContext(RuleType.PCT_CHANGE, threshold=5, param_a=0, param_b=0)
    state = _state(change_pct=7.2)
    assert evaluate_rule(rule, state).triggered


def test_pct_change_ignores_small_move():
    rule = RuleContext(RuleType.PCT_CHANGE, threshold=5, param_a=0, param_b=0)
    state = _state(change_pct=1.0)
    assert not evaluate_rule(rule, state).triggered


def test_rsi_overbought_triggers_on_strong_uptrend():
    rule = RuleContext(RuleType.RSI_OVERBOUGHT, threshold=70, param_a=14, param_b=0)
    closes = list(np.linspace(100, 200, 40))  # strong sustained uptrend -> high RSI
    state = _state(closes=closes)
    assert evaluate_rule(rule, state).triggered


def test_rsi_oversold_triggers_on_strong_downtrend():
    rule = RuleContext(RuleType.RSI_OVERSOLD, threshold=30, param_a=14, param_b=0)
    closes = list(np.linspace(200, 100, 40))  # strong sustained downtrend -> low RSI
    state = _state(closes=closes)
    assert evaluate_rule(rule, state).triggered


def test_ma_cross_up_detects_golden_cross():
    rule = RuleContext(RuleType.MA_CROSS_UP, threshold=0, param_a=3, param_b=10)
    # flat (fast == slow, diff == 0) then a jump on the very last bar so the
    # fast EMA crosses above the slow EMA exactly between the last two points
    closes = [100] * 20 + [110]
    state = _state(closes=closes)
    result = evaluate_rule(rule, state)
    assert result.triggered


def test_ma_cross_up_no_trigger_on_flat_series():
    rule = RuleContext(RuleType.MA_CROSS_UP, threshold=0, param_a=3, param_b=10)
    closes = [100] * 30
    state = _state(closes=closes)
    assert not evaluate_rule(rule, state).triggered


def test_volume_spike_triggers():
    rule = RuleContext(RuleType.VOLUME_SPIKE, threshold=3, param_a=20, param_b=0)
    volumes = [1000] * 25 + [10000]
    state = _state(closes=[100] * 26, volumes=volumes)
    assert evaluate_rule(rule, state).triggered


def test_volume_spike_no_trigger_on_normal_volume():
    rule = RuleContext(RuleType.VOLUME_SPIKE, threshold=3, param_a=20, param_b=0)
    volumes = [1000] * 26
    state = _state(closes=[100] * 26, volumes=volumes)
    assert not evaluate_rule(rule, state).triggered


def test_cooldown_expired_when_never_triggered():
    assert cooldown_expired(None, 60) is True


def test_cooldown_not_expired_when_recent():
    recent = datetime.now(timezone.utc) - timedelta(minutes=5)
    assert cooldown_expired(recent, 60) is False


def test_cooldown_expired_after_window():
    old = datetime.now(timezone.utc) - timedelta(minutes=120)
    assert cooldown_expired(old, 60) is True
