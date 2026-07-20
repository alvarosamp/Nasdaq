from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application

from app.config import settings
from app.db import SessionLocal
from app.dedup import filter_new_by_key
from app.market_data import finnhub_client, fmp_client, yfinance_client
from app.models import (
    AlertLog,
    AlertRule,
    EarningsEvent,
    EconomicEvent,
    NewsItem,
    PriceSnapshot,
    WatchlistItem,
)
from app.rules_engine import MarketState, RuleContext, cooldown_expired, evaluate_rule
from app.telegram_bot import send_alert

logger = logging.getLogger(__name__)


async def poll_quotes() -> None:
    db = SessionLocal()
    try:
        items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
        for item in items:
            quote = finnhub_client.get_quote(item.symbol)
            if quote is None:
                continue
            db.add(
                PriceSnapshot(
                    watchlist_item_id=item.id,
                    price=quote.price,
                    change_pct=quote.change_pct,
                    volume=quote.volume,
                )
            )
        db.commit()
    except Exception:
        logger.exception("Erro no job poll_quotes")
        db.rollback()
    finally:
        db.close()


async def evaluate_rules(telegram_app: Application | None) -> None:
    db = SessionLocal()
    try:
        items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
        for item in items:
            rules = db.query(AlertRule).filter(
                AlertRule.watchlist_item_id == item.id, AlertRule.active.is_(True)
            ).all()
            if not rules:
                continue

            latest_snapshot = (
                db.query(PriceSnapshot)
                .filter(PriceSnapshot.watchlist_item_id == item.id)
                .order_by(PriceSnapshot.taken_at.desc())
                .first()
            )
            if latest_snapshot is None:
                continue

            history = yfinance_client.get_history(item.symbol)
            if history.empty:
                continue

            state = MarketState(
                symbol=item.symbol,
                price=latest_snapshot.price,
                change_pct=latest_snapshot.change_pct,
                volume=latest_snapshot.volume,
                history=history,
            )

            for rule in rules:
                if not cooldown_expired(rule.last_triggered_at, rule.cooldown_minutes):
                    continue
                ctx = RuleContext(
                    rule_type=rule.rule_type,
                    threshold=rule.threshold,
                    param_a=rule.param_a,
                    param_b=rule.param_b,
                )
                result = evaluate_rule(ctx, state)
                if not result.triggered:
                    continue

                from app.models import utcnow

                rule.last_triggered_at = utcnow()
                log = AlertLog(symbol=item.symbol, rule_type=rule.rule_type.value, message=result.message)
                db.add(log)
                db.commit()

                delivered = await send_alert(telegram_app, f"🔔 {result.message}")
                log.delivered_telegram = delivered
                db.commit()
    except Exception:
        logger.exception("Erro no job evaluate_rules")
        db.rollback()
    finally:
        db.close()


async def refresh_news() -> None:
    db = SessionLocal()
    try:
        items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
        today = date.today()
        week_ago = today - timedelta(days=7)
        existing_urls = {u for (u,) in db.query(NewsItem.url).all()}

        for item in items:
            articles = finnhub_client.get_company_news(item.symbol, week_ago, today)
            new_articles = filter_new_by_key(articles, existing_urls, key_fn=lambda a: a.url)
            for article in new_articles:
                db.add(
                    NewsItem(
                        symbol=article.symbol,
                        headline=article.headline,
                        summary=article.summary,
                        url=article.url,
                        source=article.source,
                        published_at=article.published_at,
                    )
                )
                existing_urls.add(article.url)
        db.commit()
    except Exception:
        logger.exception("Erro no job refresh_news")
        db.rollback()
    finally:
        db.close()


async def refresh_calendars() -> None:
    db = SessionLocal()
    try:
        today = date.today()

        econ_events = fmp_client.get_economic_calendar(today, today + timedelta(days=7))
        existing_econ_keys = {
            (name, country, dt) for name, country, dt in db.query(
                EconomicEvent.event_name, EconomicEvent.country, EconomicEvent.event_date
            ).all()
        }
        new_econ = filter_new_by_key(
            econ_events, existing_econ_keys, key_fn=lambda e: (e.event_name, e.country, e.event_date)
        )
        for event in new_econ:
            db.add(
                EconomicEvent(
                    event_name=event.event_name,
                    country=event.country,
                    event_date=event.event_date,
                    impact=event.impact,
                    actual=event.actual,
                    forecast=event.forecast,
                    previous=event.previous,
                )
            )

        items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
        existing_earnings_keys = {
            (sym, dt) for sym, dt in db.query(EarningsEvent.symbol, EarningsEvent.event_date).all()
        }
        for item in items:
            earnings = finnhub_client.get_earnings_calendar(
                today, today + timedelta(days=14), symbol=item.symbol
            )
            new_earnings = filter_new_by_key(
                earnings, existing_earnings_keys, key_fn=lambda e: (e.symbol, e.event_date)
            )
            for entry in new_earnings:
                db.add(
                    EarningsEvent(
                        symbol=entry.symbol,
                        event_date=entry.event_date,
                        eps_estimate=entry.eps_estimate,
                        revenue_estimate=entry.revenue_estimate,
                    )
                )
                existing_earnings_keys.add((entry.symbol, entry.event_date))

        db.commit()
    except Exception:
        logger.exception("Erro no job refresh_calendars")
        db.rollback()
    finally:
        db.close()


async def daily_summary(telegram_app: Application | None) -> None:
    db = SessionLocal()
    try:
        items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
        if not items:
            return

        now = datetime.now(timezone.utc)
        lines = ["📊 Resumo do dia:"]
        for item in items:
            snap = (
                db.query(PriceSnapshot)
                .filter(PriceSnapshot.watchlist_item_id == item.id)
                .order_by(PriceSnapshot.taken_at.desc())
                .first()
            )
            if snap:
                arrow = "🔺" if snap.change_pct >= 0 else "🔻"
                lines.append(f"{item.symbol}: {snap.price:.2f} {arrow} {snap.change_pct:+.2f}%")

        since = now - timedelta(hours=24)
        news = (
            db.query(NewsItem)
            .filter(NewsItem.published_at >= since)
            .order_by(NewsItem.published_at.desc())
            .limit(5)
            .all()
        )
        if news:
            lines.append("\n📰 Notícias das últimas 24h:")
            lines.extend(f"• {n.symbol}: {n.headline}" for n in news)

        econ_today = (
            db.query(EconomicEvent)
            .filter(
                EconomicEvent.event_date >= now.replace(hour=0, minute=0, second=0, microsecond=0),
                EconomicEvent.event_date < now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1),
                EconomicEvent.impact == "high",
            )
            .all()
        )
        if econ_today:
            lines.append("\n🌎 Eventos econômicos de alto impacto hoje:")
            lines.extend(f"• {e.event_name} ({e.country})" for e in econ_today)

        upcoming_earnings = (
            db.query(EarningsEvent)
            .filter(EarningsEvent.event_date >= now, EarningsEvent.event_date <= now + timedelta(days=7))
            .order_by(EarningsEvent.event_date)
            .all()
        )
        if upcoming_earnings:
            lines.append("\n📅 Earnings da watchlist nos próximos 7 dias:")
            lines.extend(f"• {e.symbol}: {e.event_date.strftime('%d/%m')}" for e in upcoming_earnings)

        await send_alert(telegram_app, "\n".join(lines))
    finally:
        db.close()


def build_scheduler(telegram_app: Application | None) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(poll_quotes, "interval", seconds=settings.quote_poll_seconds, id="poll_quotes")
    scheduler.add_job(
        evaluate_rules,
        "interval",
        seconds=settings.indicator_refresh_seconds,
        args=[telegram_app],
        id="evaluate_rules",
    )
    scheduler.add_job(
        daily_summary,
        "cron",
        hour=settings.daily_summary_hour_utc,
        minute=0,
        args=[telegram_app],
        id="daily_summary",
    )
    scheduler.add_job(refresh_news, "interval", seconds=settings.news_refresh_seconds, id="refresh_news")
    scheduler.add_job(
        refresh_calendars,
        "cron",
        hour=settings.calendar_refresh_hour_utc,
        minute=0,
        id="refresh_calendars",
    )
    return scheduler
