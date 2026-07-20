from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import require_login
from app.db import get_db
from app.models import AlertLog, EarningsEvent, EconomicEvent, NewsItem, PriceSnapshot, RuleType, User, WatchlistItem
from app.reports import build_pdf_report

router = APIRouter(dependencies=[Depends(require_login)])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def dashboard_home(request: Request, db: Session = Depends(get_db), user: User = Depends(require_login)):
    items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
    rows = []
    for item in items:
        snap = (
            db.query(PriceSnapshot)
            .filter(PriceSnapshot.watchlist_item_id == item.id)
            .order_by(PriceSnapshot.taken_at.desc())
            .first()
        )
        rows.append({"item": item, "snapshot": snap})

    recent_alerts = db.query(AlertLog).order_by(AlertLog.triggered_at.desc()).limit(20).all()

    now = datetime.now(timezone.utc)
    upcoming_earnings = (
        db.query(EarningsEvent)
        .filter(EarningsEvent.event_date >= now, EarningsEvent.event_date <= now + timedelta(days=7))
        .order_by(EarningsEvent.event_date)
        .limit(10)
        .all()
    )
    upcoming_econ = (
        db.query(EconomicEvent)
        .filter(EconomicEvent.event_date >= now, EconomicEvent.event_date <= now + timedelta(days=7))
        .order_by(EconomicEvent.event_date)
        .limit(10)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "rows": rows,
            "alerts": recent_alerts,
            "upcoming_earnings": upcoming_earnings,
            "upcoming_econ": upcoming_econ,
            "user": user,
        },
    )


@router.get("/mercado")
def market_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_login)):
    now = datetime.now(timezone.utc)

    news = db.query(NewsItem).order_by(NewsItem.published_at.desc()).limit(40).all()
    econ_events = (
        db.query(EconomicEvent)
        .filter(EconomicEvent.event_date >= now - timedelta(days=1))
        .order_by(EconomicEvent.event_date)
        .limit(50)
        .all()
    )
    earnings_events = (
        db.query(EarningsEvent)
        .filter(EarningsEvent.event_date >= now - timedelta(days=1))
        .order_by(EarningsEvent.event_date)
        .limit(50)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "market.html",
        {"news": news, "econ_events": econ_events, "earnings_events": earnings_events, "user": user},
    )


@router.get("/ativo/{symbol}")
def asset_detail(request: Request, symbol: str, user: User = Depends(require_login)):
    return templates.TemplateResponse(request, "asset.html", {"symbol": symbol.upper(), "user": user})


@router.get("/watchlist")
def watchlist_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_login)):
    items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
    return templates.TemplateResponse(request, "watchlist.html", {"items": items, "user": user})


@router.get("/alertas")
def alerts_page(request: Request, db: Session = Depends(get_db), user: User = Depends(require_login)):
    symbols = [s for (s,) in db.query(WatchlistItem.symbol).order_by(WatchlistItem.symbol).all()]
    rule_types = [rt.value for rt in RuleType]
    return templates.TemplateResponse(
        request, "alerts.html", {"symbols": symbols, "rule_types": rule_types, "user": user}
    )


@router.get("/posicoes")
def positions_page(request: Request, user: User = Depends(require_login)):
    return templates.TemplateResponse(request, "positions.html", {"user": user})


@router.get("/assistente")
def assistant_page(request: Request, user: User = Depends(require_login)):
    return templates.TemplateResponse(request, "assistant.html", {"user": user})


@router.get("/relatorio.pdf")
def download_report(db: Session = Depends(get_db)):
    pdf_bytes = build_pdf_report(db)
    filename = f"monitor-nasdaq-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
