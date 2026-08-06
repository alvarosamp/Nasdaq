from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.data_quality import validate_watchlist_data
from app.db import get_db
from app.market_data import yfinance_client
from app.models import AlertLog, AuditLog, PriceSnapshot

router = APIRouter(prefix="/api/operations", tags=["operations"], dependencies=[Depends(get_current_user)])


@router.get("/health")
def operational_health(db: Session = Depends(get_db)):
    latest_snapshot = db.query(PriceSnapshot).order_by(PriceSnapshot.taken_at.desc()).first()
    now = datetime.now(timezone.utc)
    latest_at = latest_snapshot.taken_at if latest_snapshot else None
    if latest_at and latest_at.tzinfo is None:
        latest_at = latest_at.replace(tzinfo=timezone.utc)
    snapshot_age_minutes = ((now - latest_at).total_seconds() / 60) if latest_at else None
    alerts = db.query(AlertLog).order_by(AlertLog.triggered_at.desc()).limit(10).all()
    audits = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(20).all()
    data_quality = validate_watchlist_data(db)
    yfinance_probe = yfinance_client.get_history("AAPL", period="5d", interval="1d")
    return {
        "status": "ok",
        "latest_snapshot_at": latest_at.isoformat() if latest_at else None,
        "snapshot_age_minutes": round(snapshot_age_minutes, 1) if snapshot_age_minutes is not None else None,
        "providers": {
            "finnhub_configured": bool(settings.finnhub_api_key),
            "fmp_configured": bool(settings.fmp_api_key),
            "yfinance_enabled": True,
            "yfinance_required_for_technical_analysis": yfinance_client.REQUIRED_FOR_TECHNICAL_ANALYSIS,
            "yfinance_available": not yfinance_probe.empty,
            "yfinance_role": yfinance_client.PROVIDER_ROLE,
        },
        "jobs": {
            "quote_poll_seconds": settings.quote_poll_seconds,
            "indicator_refresh_seconds": settings.indicator_refresh_seconds,
            "news_refresh_seconds": settings.news_refresh_seconds,
            "radar_bot_hour_utc": settings.radar_bot_hour_utc,
            "weekly_review_bot": f"{settings.weekly_review_bot_day_of_week} {settings.weekly_review_bot_hour_utc}:00 UTC",
        },
        "data_quality": data_quality["confidence_counts"],
        "recent_alerts": [
            {"symbol": a.symbol, "message": a.message, "triggered_at": a.triggered_at.isoformat()} for a in alerts
        ],
        "recent_audit_logs": [
            {
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "created_at": a.created_at.isoformat(),
            }
            for a in audits
        ],
    }
