from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.market_data import finnhub_client, yfinance_client
from app.models import PriceSnapshot, WatchlistItem


@dataclass
class ProviderCheck:
    provider: str
    available: bool
    price: float | None = None
    change_pct: float | None = None
    timestamp: datetime | None = None
    error: str = ""


def _latest_snapshot(db: Session, symbol: str) -> PriceSnapshot | None:
    item = db.query(WatchlistItem).filter(WatchlistItem.symbol == symbol.upper()).first()
    if item is None:
        return None
    return (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.watchlist_item_id == item.id)
        .order_by(PriceSnapshot.taken_at.desc())
        .first()
    )


def _aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def check_finnhub(symbol: str) -> ProviderCheck:
    try:
        quote = finnhub_client.get_quote(symbol)
    except Exception as exc:
        return ProviderCheck("finnhub", False, error=str(exc))
    if quote is None:
        return ProviderCheck("finnhub", False, error="Sem cotacao")
    return ProviderCheck("finnhub", True, quote.price, quote.change_pct, datetime.now(timezone.utc))


def check_yfinance(symbol: str) -> ProviderCheck:
    history = yfinance_client.get_history(symbol, period="5d", interval="1d")
    if history.empty:
        return ProviderCheck("yfinance", False, error="Sem historico")
    close = history["close"].dropna()
    if close.empty:
        return ProviderCheck("yfinance", False, error="Sem fechamento")
    latest = float(close.iloc[-1])
    previous = float(close.iloc[-2]) if len(close) >= 2 else latest
    change_pct = ((latest - previous) / previous * 100) if previous else 0.0
    ts = close.index[-1]
    timestamp = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return ProviderCheck("yfinance", True, latest, change_pct, timestamp)


def validate_symbol_data(db: Session, symbol: str) -> dict:
    symbol = symbol.upper().strip()
    checks = [check_finnhub(symbol), check_yfinance(symbol)]
    latest_local = _latest_snapshot(db, symbol)
    if latest_local:
        checks.append(
            ProviderCheck(
                "local_snapshot",
                True,
                latest_local.price,
                latest_local.change_pct,
                _aware_utc(latest_local.taken_at),
            )
        )

    available = [check for check in checks if check.available and check.price is not None]
    prices = [check.price for check in available if check.price is not None]
    reference = prices[0] if prices else None
    max_divergence_pct = 0.0
    if reference:
        max_divergence_pct = max(abs((price - reference) / reference * 100) for price in prices)

    now = datetime.now(timezone.utc)
    freshest = None
    if available:
        timestamps = [_aware_utc(check.timestamp) for check in available if check.timestamp is not None]
        timestamps = [ts for ts in timestamps if ts is not None]
        freshest = max(timestamps) if timestamps else None
    age_minutes = ((now - freshest).total_seconds() / 60) if freshest else None

    issues = []
    if len(available) < 2:
        issues.append("Menos de duas fontes disponiveis para comparacao.")
    if max_divergence_pct > 1:
        issues.append(f"Divergencia alta entre fontes: {max_divergence_pct:.2f}%.")
    if age_minutes is not None and age_minutes > 24 * 60:
        issues.append(f"Dado mais recente tem {age_minutes:.0f} minutos.")

    if not available:
        confidence = "LOW"
    elif issues:
        confidence = "MEDIUM"
    else:
        confidence = "HIGH"

    return {
        "symbol": symbol,
        "confidence": confidence,
        "max_divergence_pct": round(max_divergence_pct, 4),
        "freshest_age_minutes": round(age_minutes, 1) if age_minutes is not None else None,
        "issues": issues,
        "providers": [
            {
                "provider": check.provider,
                "available": check.available,
                "price": round(check.price, 4) if check.price is not None else None,
                "change_pct": round(check.change_pct, 4) if check.change_pct is not None else None,
                "timestamp": check.timestamp.isoformat() if check.timestamp else None,
                "error": check.error,
            }
            for check in checks
        ],
    }


def validate_watchlist_data(db: Session) -> dict:
    items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
    rows = [validate_symbol_data(db, item.symbol) for item in items]
    confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for row in rows:
        confidence_counts[row["confidence"]] += 1
    return {"rows": rows, "confidence_counts": confidence_counts}


def quality_gate(db: Session, symbol: str, min_confidence: str = "MEDIUM") -> dict:
    levels = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    result = validate_symbol_data(db, symbol)
    allowed = levels[result["confidence"]] >= levels[min_confidence]
    return {
        "allowed": allowed,
        "required_confidence": min_confidence,
        "reason": "" if allowed else "Qualidade de dados insuficiente para analise automatica.",
        **result,
    }
