"""Builds a PDF snapshot of the monitoring dashboard: watchlist, alerts,
news and upcoming economic/earnings events. Pure function of a DB session so
it's usable both from the web route and from the Telegram /relatorio command.
"""
from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.models import AlertLog, EarningsEvent, EconomicEvent, NewsItem, PriceSnapshot, WatchlistItem


def build_pdf_report(db: Session) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    muted = ParagraphStyle("muted", parent=styles["Normal"], textColor=colors.grey, fontSize=8)

    now = datetime.now(timezone.utc)
    story = []

    story.append(Paragraph("Monitor NASDAQ — Relatório", styles["Title"]))
    story.append(Paragraph(f"Gerado em {now.strftime('%d/%m/%Y %H:%M UTC')}", muted))
    story.append(Spacer(1, 0.5 * cm))

    # Watchlist
    story.append(Paragraph("Watchlist", styles["Heading2"]))
    items = db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()
    rows = [["Símbolo", "Preço", "Variação", "Atualizado"]]
    for item in items:
        snap = (
            db.query(PriceSnapshot)
            .filter(PriceSnapshot.watchlist_item_id == item.id)
            .order_by(PriceSnapshot.taken_at.desc())
            .first()
        )
        if snap:
            rows.append(
                [
                    item.symbol,
                    f"{snap.price:.2f}",
                    f"{snap.change_pct:+.2f}%",
                    snap.taken_at.strftime("%d/%m %H:%M UTC"),
                ]
            )
        else:
            rows.append([item.symbol, "-", "-", "sem dados"])
    if len(rows) == 1:
        rows.append(["(watchlist vazia)", "", "", ""])
    story.append(_styled_table(rows))
    story.append(Spacer(1, 0.5 * cm))

    # Recent alerts
    story.append(Paragraph("Alertas recentes", styles["Heading2"]))
    alerts = db.query(AlertLog).order_by(AlertLog.triggered_at.desc()).limit(15).all()
    if alerts:
        alert_rows = [["Data", "Símbolo", "Mensagem"]]
        for a in alerts:
            alert_rows.append([a.triggered_at.strftime("%d/%m %H:%M"), a.symbol, a.message])
        story.append(_styled_table(alert_rows, col_widths=[2.5 * cm, 2 * cm, 11 * cm]))
    else:
        story.append(Paragraph("Nenhum alerta disparado ainda.", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # News
    story.append(Paragraph("Notícias recentes", styles["Heading2"]))
    since = now - timedelta(hours=48)
    news = (
        db.query(NewsItem)
        .filter(NewsItem.published_at >= since)
        .order_by(NewsItem.published_at.desc())
        .limit(15)
        .all()
    )
    if news:
        for n in news:
            story.append(
                Paragraph(
                    f"<b>{n.symbol}</b> ({n.published_at.strftime('%d/%m %H:%M')}) — {n.headline}",
                    styles["Normal"],
                )
            )
    else:
        story.append(Paragraph("Nenhuma notícia recente coletada.", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # Upcoming economic events
    story.append(Paragraph("Calendário econômico (próximos 7 dias)", styles["Heading2"]))
    econ = (
        db.query(EconomicEvent)
        .filter(EconomicEvent.event_date >= now, EconomicEvent.event_date <= now + timedelta(days=7))
        .order_by(EconomicEvent.event_date)
        .limit(20)
        .all()
    )
    if econ:
        econ_rows = [["Data", "Evento", "País", "Impacto"]]
        for e in econ:
            econ_rows.append([e.event_date.strftime("%d/%m %H:%M"), e.event_name, e.country, e.impact])
        story.append(_styled_table(econ_rows, col_widths=[2.5 * cm, 8 * cm, 2.5 * cm, 2.5 * cm]))
    else:
        story.append(Paragraph("Nenhum evento econômico carregado.", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # Upcoming earnings
    story.append(Paragraph("Earnings da watchlist (próximos 7 dias)", styles["Heading2"]))
    earnings = (
        db.query(EarningsEvent)
        .filter(EarningsEvent.event_date >= now, EarningsEvent.event_date <= now + timedelta(days=7))
        .order_by(EarningsEvent.event_date)
        .limit(20)
        .all()
    )
    if earnings:
        earn_rows = [["Data", "Símbolo", "EPS estimado"]]
        for e in earnings:
            eps = f"{e.eps_estimate:.2f}" if e.eps_estimate is not None else "-"
            earn_rows.append([e.event_date.strftime("%d/%m"), e.symbol, eps])
        story.append(_styled_table(earn_rows, col_widths=[2.5 * cm, 3 * cm, 3 * cm]))
    else:
        story.append(Paragraph("Nenhum earnings carregado.", styles["Normal"]))

    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(
            "Ferramenta apenas de monitoramento e sugestão. Não executa ordens e não constitui "
            "recomendação de investimento. Dados podem ter atraso. Valide qualquer sinal antes "
            "de decidir.",
            muted,
        )
    )

    doc.build(story)
    return buffer.getvalue()


def _styled_table(rows: list[list[str]], col_widths: list[float] | None = None) -> Table:
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ]
        )
    )
    return table
