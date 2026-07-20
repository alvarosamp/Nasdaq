"""Evaluates AlertRule objects against the latest market data for a symbol.

Kept as pure functions operating on plain values/DataFrames so it can be
unit-tested without touching the database or a live market data API.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

from app import indicators
from app.models import RuleType


@dataclass
class MarketState:
    symbol: str
    price: float
    change_pct: float
    volume: float
    history: pd.DataFrame  # columns: close, volume ; DatetimeIndex, ascending


@dataclass
class RuleContext:
    rule_type: RuleType
    threshold: float
    param_a: int
    param_b: int


@dataclass
class RuleResult:
    triggered: bool
    message: str = ""


def evaluate_rule(rule: RuleContext, state: MarketState) -> RuleResult:
    handler = _HANDLERS.get(rule.rule_type)
    if handler is None:
        return RuleResult(False)
    return handler(rule, state)


def _price_above(rule: RuleContext, state: MarketState) -> RuleResult:
    if state.price > rule.threshold:
        return RuleResult(True, f"{state.symbol}: preço {state.price:.2f} ultrapassou {rule.threshold:.2f}")
    return RuleResult(False)


def _price_below(rule: RuleContext, state: MarketState) -> RuleResult:
    if state.price < rule.threshold:
        return RuleResult(True, f"{state.symbol}: preço {state.price:.2f} caiu abaixo de {rule.threshold:.2f}")
    return RuleResult(False)


def _pct_change(rule: RuleContext, state: MarketState) -> RuleResult:
    if abs(state.change_pct) >= rule.threshold:
        direction = "subiu" if state.change_pct > 0 else "caiu"
        return RuleResult(
            True,
            f"{state.symbol}: {direction} {abs(state.change_pct):.2f}% (limite {rule.threshold:.2f}%)",
        )
    return RuleResult(False)


def _rsi_overbought(rule: RuleContext, state: MarketState) -> RuleResult:
    period = rule.param_a or 14
    series = indicators.rsi(state.history["close"], period=period)
    if series.empty or pd.isna(series.iloc[-1]):
        return RuleResult(False)
    value = series.iloc[-1]
    limit = rule.threshold or 70
    if value >= limit:
        return RuleResult(True, f"{state.symbol}: RSI({period}) em {value:.1f}, sobrecomprado (>= {limit:.0f})")
    return RuleResult(False)


def _rsi_oversold(rule: RuleContext, state: MarketState) -> RuleResult:
    period = rule.param_a or 14
    series = indicators.rsi(state.history["close"], period=period)
    if series.empty or pd.isna(series.iloc[-1]):
        return RuleResult(False)
    value = series.iloc[-1]
    limit = rule.threshold or 30
    if value <= limit:
        return RuleResult(True, f"{state.symbol}: RSI({period}) em {value:.1f}, sobrevendido (<= {limit:.0f})")
    return RuleResult(False)


def _ma_cross(rule: RuleContext, state: MarketState, direction: str) -> RuleResult:
    fast_p = rule.param_a or 9
    slow_p = rule.param_b or 21
    fast = indicators.ema(state.history["close"], fast_p)
    slow = indicators.ema(state.history["close"], slow_p)
    if len(fast) < 2 or pd.isna(fast.iloc[-2]) or pd.isna(slow.iloc[-2]):
        return RuleResult(False)

    prev_diff = fast.iloc[-2] - slow.iloc[-2]
    curr_diff = fast.iloc[-1] - slow.iloc[-1]

    if direction == "up" and prev_diff <= 0 < curr_diff:
        return RuleResult(True, f"{state.symbol}: EMA{fast_p} cruzou ACIMA da EMA{slow_p} (golden cross)")
    if direction == "down" and prev_diff >= 0 > curr_diff:
        return RuleResult(True, f"{state.symbol}: EMA{fast_p} cruzou ABAIXO da EMA{slow_p} (death cross)")
    return RuleResult(False)


def _ma_cross_up(rule: RuleContext, state: MarketState) -> RuleResult:
    return _ma_cross(rule, state, "up")


def _ma_cross_down(rule: RuleContext, state: MarketState) -> RuleResult:
    return _ma_cross(rule, state, "down")


def _macd_cross(rule: RuleContext, state: MarketState, direction: str) -> RuleResult:
    macd_df = indicators.macd(state.history["close"])
    if len(macd_df) < 2 or macd_df["macd"].iloc[-2:].isna().any() or macd_df["signal"].iloc[-2:].isna().any():
        return RuleResult(False)

    prev_diff = macd_df["macd"].iloc[-2] - macd_df["signal"].iloc[-2]
    curr_diff = macd_df["macd"].iloc[-1] - macd_df["signal"].iloc[-1]

    if direction == "up" and prev_diff <= 0 < curr_diff:
        return RuleResult(True, f"{state.symbol}: MACD cruzou ACIMA da linha de sinal (possível alta)")
    if direction == "down" and prev_diff >= 0 > curr_diff:
        return RuleResult(True, f"{state.symbol}: MACD cruzou ABAIXO da linha de sinal (possível baixa)")
    return RuleResult(False)


def _macd_cross_up(rule: RuleContext, state: MarketState) -> RuleResult:
    return _macd_cross(rule, state, "up")


def _macd_cross_down(rule: RuleContext, state: MarketState) -> RuleResult:
    return _macd_cross(rule, state, "down")


def _volume_spike(rule: RuleContext, state: MarketState) -> RuleResult:
    period = rule.param_a or 20
    ratio_series = indicators.volume_ratio(state.history["volume"], period=period)
    if ratio_series.empty or pd.isna(ratio_series.iloc[-1]):
        return RuleResult(False)
    ratio = ratio_series.iloc[-1]
    multiple = rule.threshold or 3.0
    if ratio >= multiple:
        return RuleResult(True, f"{state.symbol}: volume {ratio:.1f}x acima da média ({period} períodos)")
    return RuleResult(False)


_HANDLERS = {
    RuleType.PRICE_ABOVE: _price_above,
    RuleType.PRICE_BELOW: _price_below,
    RuleType.PCT_CHANGE: _pct_change,
    RuleType.RSI_OVERBOUGHT: _rsi_overbought,
    RuleType.RSI_OVERSOLD: _rsi_oversold,
    RuleType.MA_CROSS_UP: _ma_cross_up,
    RuleType.MA_CROSS_DOWN: _ma_cross_down,
    RuleType.MACD_CROSS_UP: _macd_cross_up,
    RuleType.MACD_CROSS_DOWN: _macd_cross_down,
    RuleType.VOLUME_SPIKE: _volume_spike,
}


def cooldown_expired(last_triggered_at: datetime | None, cooldown_minutes: int) -> bool:
    if last_triggered_at is None:
        return True
    now = datetime.now(timezone.utc)
    if last_triggered_at.tzinfo is None:
        last_triggered_at = last_triggered_at.replace(tzinfo=timezone.utc)
    elapsed_minutes = (now - last_triggered_at).total_seconds() / 60
    return elapsed_minutes >= cooldown_minutes
