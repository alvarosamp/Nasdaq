"""Position/P&L accounting from a manual transaction log.

Pure functions only — no DB access — so they're trivial to unit test. Uses
the weighted-average-cost method (not FIFO lots): every BUY recomputes the
average cost, every SELL realizes P&L against the current average cost and
leaves the average cost itself unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.models import TransactionSide


class TransactionLike(Protocol):
    side: TransactionSide
    quantity: float
    price: float
    executed_at: object  # anything sortable (datetime)


@dataclass
class PositionSummary:
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float | None
    market_value: float | None
    unrealized_pnl: float | None
    realized_pnl: float


def compute_position(symbol: str, transactions: list[TransactionLike], current_price: float | None) -> PositionSummary:
    quantity = 0.0
    avg_cost = 0.0
    realized_pnl = 0.0

    for tx in sorted(transactions, key=lambda t: t.executed_at):
        if tx.side == TransactionSide.BUY:
            new_quantity = quantity + tx.quantity
            if new_quantity > 0:
                avg_cost = (avg_cost * quantity + tx.price * tx.quantity) / new_quantity
            quantity = new_quantity
        else:  # SELL
            realized_pnl += (tx.price - avg_cost) * tx.quantity
            quantity -= tx.quantity

    if abs(quantity) < 1e-9:
        quantity = 0.0
        avg_cost = 0.0
        market_value = 0.0
        unrealized_pnl = 0.0
    else:
        market_value = quantity * current_price if current_price is not None else None
        unrealized_pnl = (current_price - avg_cost) * quantity if current_price is not None else None

    return PositionSummary(
        symbol=symbol,
        quantity=round(quantity, 6),
        avg_cost=round(avg_cost, 4),
        current_price=current_price,
        market_value=round(market_value, 2) if market_value is not None else None,
        unrealized_pnl=round(unrealized_pnl, 2) if unrealized_pnl is not None else None,
        realized_pnl=round(realized_pnl, 2),
    )
