"""Telegram bot: sends alerts and lets the authorized user manage the watchlist.

Restricted to a single whitelisted chat id (settings.telegram_chat_id) so a
stranger who finds the bot username can't read/alter the watchlist.
"""
from __future__ import annotations

import io
import logging
from datetime import datetime, timezone

from telegram import InputFile, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import settings
from app.db import SessionLocal
from app.models import WatchlistItem

logger = logging.getLogger(__name__)


def _is_authorized(update: Update) -> bool:
    if not settings.telegram_chat_id:
        return True  # no whitelist configured (dev mode)
    return str(update.effective_chat.id) == str(settings.telegram_chat_id)


async def _guard(update: Update) -> bool:
    if not _is_authorized(update):
        await update.message.reply_text("Não autorizado.")
        return False
    return True


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    await update.message.reply_text(
        "Monitor NASDAQ ativo.\n\n"
        "Comandos:\n"
        "/watchlist - lista os ativos monitorados\n"
        "/add SYMBOL - adiciona um ativo (ex: /add AAPL)\n"
        "/remove SYMBOL - remove um ativo\n"
        "/status - resumo rápido dos preços atuais\n"
        "/relatorio - gera e envia um relatório em PDF\n"
        "/matinal - gera e envia a análise matinal (índices, níveis, noticias e calendário do dia)\n"
        "/pergunta <texto> - pergunta ao assistente de IA sobre a watchlist\n"
        f"\nSeu chat_id: {update.effective_chat.id}"
    )


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    db = SessionLocal()
    try:
        items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
        if not items:
            await update.message.reply_text("Watchlist vazia. Use /add SYMBOL para adicionar.")
            return
        lines = [f"• {i.symbol} {('- ' + i.label) if i.label else ''}" for i in items]
        await update.message.reply_text("Watchlist:\n" + "\n".join(lines))
    finally:
        db.close()


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    if not context.args:
        await update.message.reply_text("Uso: /add SYMBOL (ex: /add AAPL)")
        return
    symbol = context.args[0].upper().strip()
    db = SessionLocal()
    try:
        existing = db.query(WatchlistItem).filter(WatchlistItem.symbol == symbol).first()
        if existing:
            existing.active = True
            db.commit()
            await update.message.reply_text(f"{symbol} reativado na watchlist.")
            return
        db.add(WatchlistItem(symbol=symbol))
        db.commit()
        await update.message.reply_text(f"{symbol} adicionado à watchlist.")
    finally:
        db.close()


async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    if not context.args:
        await update.message.reply_text("Uso: /remove SYMBOL")
        return
    symbol = context.args[0].upper().strip()
    db = SessionLocal()
    try:
        item = db.query(WatchlistItem).filter(WatchlistItem.symbol == symbol).first()
        if not item:
            await update.message.reply_text(f"{symbol} não está na watchlist.")
            return
        item.active = False
        db.commit()
        await update.message.reply_text(f"{symbol} removido da watchlist.")
    finally:
        db.close()


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    from app.models import PriceSnapshot

    db = SessionLocal()
    try:
        items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
        if not items:
            await update.message.reply_text("Watchlist vazia.")
            return
        lines = []
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
            else:
                lines.append(f"{item.symbol}: sem dados ainda")
        await update.message.reply_text("Status:\n" + "\n".join(lines))
    finally:
        db.close()


async def cmd_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    from app.reports import build_pdf_report

    await update.message.reply_text("Gerando relatório em PDF...")
    db = SessionLocal()
    try:
        pdf_bytes = build_pdf_report(db)
    finally:
        db.close()

    filename = f"monitor-nasdaq-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}.pdf"
    await update.message.reply_document(document=InputFile(io.BytesIO(pdf_bytes), filename=filename))


async def cmd_matinal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    from app import morning_report

    await update.message.reply_chat_action("typing")
    db = SessionLocal()
    try:
        report = await morning_report.generate_and_store(db)
    finally:
        db.close()
    await update.message.reply_text(f"☀️ {report.narrative}")


async def cmd_pergunta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard(update):
        return
    if not context.args:
        await update.message.reply_text("Uso: /pergunta sua pergunta aqui (ex: /pergunta por que a AAPL caiu hoje?)")
        return

    from app.llm_client import answer_question
    from app.routers.assistant import build_assistant_context

    question = " ".join(context.args)
    await update.message.reply_chat_action("typing")

    db = SessionLocal()
    try:
        ctx = build_assistant_context(db)
    finally:
        db.close()

    answer = await answer_question(question, ctx)
    await update.message.reply_text(answer)


def build_application() -> Application | None:
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN não configurado — bot do Telegram desativado.")
        return None

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_start))
    application.add_handler(CommandHandler("watchlist", cmd_watchlist))
    application.add_handler(CommandHandler("add", cmd_add))
    application.add_handler(CommandHandler("remove", cmd_remove))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("relatorio", cmd_relatorio))
    application.add_handler(CommandHandler("matinal", cmd_matinal))
    application.add_handler(CommandHandler("pergunta", cmd_pergunta))
    return application


async def send_alert(application: Application | None, message: str) -> bool:
    if application is None or not settings.telegram_chat_id:
        return False
    try:
        await application.bot.send_message(chat_id=settings.telegram_chat_id, text=message)
        return True
    except Exception:
        logger.exception("Falha ao enviar alerta via Telegram")
        return False
