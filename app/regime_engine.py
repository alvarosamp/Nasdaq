"""Market regime engine — Level 1 (per-asset local regime) and Level 2
(cross-asset/macro overlay), as scoped in the platform architecture plan.

Deterministic and rule-based on purpose: this feeds the AI copilot and the
future confidence engine, and neither may originate its own price/trend
read — they consume this module's output instead. Weights below are
hand-picked defaults, not validated; app/backtest.py-style quant validation
against real outcomes should replace them before this drives real trading
decisions (tracked as a follow-up, not solved here).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sqlalchemy.orm import Session

from app import indicators
from app.market_data import macro_data, yfinance_client
from app.models import MacroSnapshot

LOCAL_REGIME_LABELS = ("STRONG BEAR", "BEAR", "NEUTRAL", "BULL", "STRONG BULL")

# Instruments considered when explaining the Nasdaq's macro context. Kept
# separate from the full MACRO_INSTRUMENTS registry because not every
# tracked instrument is a useful cross-check for every target asset.
NASDAQ_CROSS_ASSETS = ("DXY", "US10Y", "GOLD", "SP500", "WTI")

RELEVANCE_HIGH = 0.5
RELEVANCE_MEDIUM = 0.25


@dataclass
class LocalRegime:
    label: str
    score: float
    factors: list[dict]


def local_regime(history: pd.DataFrame) -> LocalRegime | None:
    """Classifies trend/momentum/volatility/structure into one of
    LOCAL_REGIME_LABELS. `history` needs open/high/low/close columns (as
    returned by yfinance_client.get_history), ideally 60+ bars.
    """
    if history.empty or len(history) < 55:
        return None

    close, high, low = history["close"], history["high"], history["low"]
    ema20 = indicators.ema(close, 20)
    ema50 = indicators.ema(close, 50)
    rsi = indicators.rsi(close, 14)
    adx_df = indicators.adx(high, low, close, 14)
    swings = indicators.swing_levels(history, lookback=20)

    last_ema20, last_ema50 = ema20.iloc[-1], ema50.iloc[-1]
    last_rsi = rsi.iloc[-1]
    last_adx = adx_df["adx"].iloc[-1]
    last_close = float(close.iloc[-1])

    if pd.isna(last_ema20) or pd.isna(last_ema50) or pd.isna(last_rsi):
        return None

    factors = []
    score = 0.0

    trend_up = last_ema20 > last_ema50
    score += 30 if trend_up else -30
    factors.append(
        {
            "name": "trend",
            "impact": 30 if trend_up else -30,
            "evidence": f"EMA20 {'acima' if trend_up else 'abaixo'} da EMA50 ({last_ema20:.2f} vs {last_ema50:.2f}).",
        }
    )

    momentum_impact = max(-25.0, min(25.0, (last_rsi - 50) * 0.7))
    score += momentum_impact
    factors.append({"name": "momentum", "impact": round(momentum_impact, 1), "evidence": f"RSI14 em {last_rsi:.1f}."})

    if not pd.isna(last_adx):
        strong_trend = last_adx >= 25
        multiplier = 1.25 if strong_trend else 0.7
        score *= multiplier
        factors.append(
            {
                "name": "forca_da_tendencia",
                "impact": None,
                "evidence": f"ADX14 em {last_adx:.1f} ({'tendencia forte' if strong_trend else 'sem tendencia definida'}), "
                f"amplifica o score em {multiplier:.2f}x.",
            }
        )

    swing_high, swing_low = swings["swing_high"], swings["swing_low"]
    if swing_high and last_close >= swing_high * 0.995:
        score += 15
        factors.append({"name": "estrutura", "impact": 15, "evidence": f"Preco proximo/rompendo maxima de 20 candles ({swing_high})."})
    elif swing_low and last_close <= swing_low * 1.005:
        score -= 15
        factors.append({"name": "estrutura", "impact": -15, "evidence": f"Preco proximo/rompendo minima de 20 candles ({swing_low})."})

    score = max(-100.0, min(100.0, score))
    if score >= 60:
        label = "STRONG BULL"
    elif score >= 20:
        label = "BULL"
    elif score <= -60:
        label = "STRONG BEAR"
    elif score <= -20:
        label = "BEAR"
    else:
        label = "NEUTRAL"

    return LocalRegime(label=label, score=round(score, 1), factors=factors)


def store_macro_snapshots(db: Session) -> int:
    """Fetches the current quote for every MACRO_INSTRUMENTS entry and
    records it. Called by the scheduler; also safe to call ad hoc.
    Returns how many were stored.
    """
    stored = 0
    for key in macro_data.MACRO_INSTRUMENTS:
        quote = macro_data.get_macro_quote(key)
        if quote is None:
            continue
        db.add(
            MacroSnapshot(
                key=key,
                symbol=quote.symbol,
                name=quote.name,
                price=quote.price,
                change_pct=quote.change_pct,
            )
        )
        stored += 1
    db.commit()
    return stored


def latest_macro_snapshot(db: Session, key: str) -> MacroSnapshot | None:
    return db.query(MacroSnapshot).filter(MacroSnapshot.key == key).order_by(MacroSnapshot.taken_at.desc()).first()


def cross_asset_relevance(db: Session, target_key: str = "NASDAQ", lookback_days: int = 30) -> list[dict]:
    """Rolling-correlation read of which cross-asset instruments currently
    matter to `target_key`. Not a fixed rulebook ("oil down = stocks up") —
    correlation and confirming/opposing direction are computed fresh from
    the last `lookback_days` of daily returns each call.
    """
    target_history = macro_data.get_macro_history(target_key, period="6mo", interval="1d")
    if target_history.empty or len(target_history) < lookback_days + 5:
        return []
    target_returns = target_history["close"].pct_change().dropna()
    target_snapshot = latest_macro_snapshot(db, target_key)

    rows = []
    for key in NASDAQ_CROSS_ASSETS:
        if key == target_key:
            continue
        other_history = macro_data.get_macro_history(key, period="6mo", interval="1d")
        if other_history.empty or len(other_history) < lookback_days + 5:
            continue
        other_returns = other_history["close"].pct_change().dropna()

        aligned = pd.concat([target_returns, other_returns], axis=1, join="inner").tail(lookback_days)
        aligned.columns = ["target", "other"]
        if len(aligned) < lookback_days * 0.6:
            continue
        corr = aligned["target"].corr(aligned["other"])
        if pd.isna(corr):
            continue

        abs_corr = abs(corr)
        if abs_corr >= RELEVANCE_HIGH:
            relevance = "ALTA"
        elif abs_corr >= RELEVANCE_MEDIUM:
            relevance = "MEDIA"
        else:
            relevance = "BAIXA"

        other_snapshot = latest_macro_snapshot(db, key)
        direction = None
        if target_snapshot and other_snapshot and abs_corr >= RELEVANCE_MEDIUM:
            same_direction_today = (target_snapshot.change_pct >= 0) == (other_snapshot.change_pct >= 0)
            expected_same_direction = corr >= 0
            direction = "CONFIRMANDO" if same_direction_today == expected_same_direction else "DIVERGINDO"

        rows.append(
            {
                "key": key,
                "name": other_snapshot.name if other_snapshot else key,
                "correlation_30d": round(float(corr), 2),
                "relevance": relevance,
                "direction": direction,
                "change_pct_latest": other_snapshot.change_pct if other_snapshot else None,
            }
        )

    return sorted(rows, key=lambda r: abs(r["correlation_30d"]), reverse=True)


def macro_context_label(cross_asset: list[dict]) -> str:
    """Rolls the cross-asset relevance table up into one POSITIVO/NEUTRO/
    NEGATIVO label for the copilot header — only instruments flagged ALTA
    or MEDIA relevance vote; a target with no relevant instruments yet
    (cold cache) reads as NEUTRO rather than a false negative.
    """
    votes = [row for row in cross_asset if row["relevance"] in ("ALTA", "MEDIA") and row["direction"]]
    if not votes:
        return "NEUTRO"
    confirming = sum(1 for v in votes if v["direction"] == "CONFIRMANDO")
    diverging = len(votes) - confirming
    if confirming > diverging:
        return "POSITIVO"
    if diverging > confirming:
        return "NEGATIVO"
    return "NEUTRO"


def regime_report(db: Session, symbol: str) -> dict:
    """Combines local regime (this symbol's own price action) with the
    macro/cross-asset overlay. `symbol` can be an equity ticker (fetched
    directly via yfinance) or a MACRO_INSTRUMENTS key (e.g. "NASDAQ").
    """
    symbol_key = symbol.upper().strip()
    if symbol_key in macro_data.MACRO_INSTRUMENTS:
        history = macro_data.get_macro_history(symbol_key, period="6mo", interval="1d")
        target_key_for_macro = symbol_key
    else:
        history = yfinance_client.get_history(symbol_key, period="6mo", interval="1d")
        target_key_for_macro = "NASDAQ"

    local = local_regime(history)
    cross_asset = cross_asset_relevance(db, target_key=target_key_for_macro)

    return {
        "symbol": symbol_key,
        "local_regime": {"label": local.label, "score": local.score, "factors": local.factors} if local else None,
        "macro_context": macro_context_label(cross_asset),
        "cross_asset_relevance": cross_asset,
    }
