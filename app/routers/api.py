import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import indicators
from app.db import get_db
from app.market_data import yfinance_client
from app.models import AlertLog, WatchlistItem
from app.schemas import AlertLogOut
from app.security import require_dashboard_auth

router = APIRouter(prefix="/api", tags=["api"], dependencies=[Depends(require_dashboard_auth)])


def _json_list(series: pd.Series, decimals: int) -> list[float | None]:
    """Convert a pandas Series to a JSON-safe list (NaN -> None)."""
    rounded = series.round(decimals)
    return [None if pd.isna(v) else float(v) for v in rounded]


@router.get("/chart/{symbol}")
def chart_data(symbol: str, period: str = "5d", interval: str = "15m"):
    history = yfinance_client.get_history(symbol.upper(), period=period, interval=interval)
    if history.empty:
        raise HTTPException(status_code=404, detail="Sem dados históricos para este símbolo")

    close = history["close"]
    rsi_series = indicators.rsi(close)
    macd_df = indicators.macd(close)
    ema_fast = indicators.ema(close, 9)
    ema_slow = indicators.ema(close, 21)

    return {
        "symbol": symbol.upper(),
        "timestamps": [ts.isoformat() for ts in history.index],
        "close": _json_list(close, 2),
        "volume": _json_list(history["volume"], 0),
        "rsi": _json_list(rsi_series, 2),
        "macd": _json_list(macd_df["macd"], 3),
        "macd_signal": _json_list(macd_df["signal"], 3),
        "ema_fast": _json_list(ema_fast, 2),
        "ema_slow": _json_list(ema_slow, 2),
    }


@router.get("/alerts", response_model=list[AlertLogOut])
def list_alerts(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(AlertLog).order_by(AlertLog.triggered_at.desc()).limit(limit).all()
