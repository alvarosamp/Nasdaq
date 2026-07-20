from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.models import TransactionSide
from app.positions import compute_position


@dataclass
class FakeTx:
    side: TransactionSide
    quantity: float
    price: float
    executed_at: datetime


def _dt(days_ago: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days_ago)


def test_no_transactions_gives_flat_position():
    result = compute_position("AAPL", [], current_price=150.0)
    assert result.quantity == 0.0
    assert result.avg_cost == 0.0
    assert result.unrealized_pnl == 0.0
    assert result.realized_pnl == 0.0


def test_single_buy_computes_avg_cost_and_unrealized_pnl():
    txs = [FakeTx(TransactionSide.BUY, 10, 100.0, _dt(5))]
    result = compute_position("AAPL", txs, current_price=120.0)
    assert result.quantity == 10
    assert result.avg_cost == 100.0
    assert result.market_value == 1200.0
    assert result.unrealized_pnl == 200.0
    assert result.realized_pnl == 0.0


def test_two_buys_average_cost_weighted():
    txs = [
        FakeTx(TransactionSide.BUY, 10, 100.0, _dt(10)),
        FakeTx(TransactionSide.BUY, 10, 120.0, _dt(5)),
    ]
    result = compute_position("AAPL", txs, current_price=130.0)
    assert result.quantity == 20
    assert result.avg_cost == 110.0  # (10*100 + 10*120) / 20


def test_partial_sell_realizes_pnl_and_keeps_avg_cost():
    txs = [
        FakeTx(TransactionSide.BUY, 10, 100.0, _dt(10)),
        FakeTx(TransactionSide.SELL, 4, 150.0, _dt(5)),
    ]
    result = compute_position("AAPL", txs, current_price=160.0)
    assert result.quantity == 6
    assert result.avg_cost == 100.0  # unchanged by the sell
    assert result.realized_pnl == 200.0  # (150-100)*4
    assert result.unrealized_pnl == 360.0  # (160-100)*6


def test_selling_everything_zeroes_the_position():
    txs = [
        FakeTx(TransactionSide.BUY, 10, 100.0, _dt(10)),
        FakeTx(TransactionSide.SELL, 10, 130.0, _dt(5)),
    ]
    result = compute_position("AAPL", txs, current_price=999.0)
    assert result.quantity == 0.0
    assert result.avg_cost == 0.0
    assert result.market_value == 0.0
    assert result.unrealized_pnl == 0.0
    assert result.realized_pnl == 300.0  # (130-100)*10


def test_transactions_processed_in_chronological_order_regardless_of_input_order():
    # SELL listed first in the input list, but it happened after the BUY
    txs = [
        FakeTx(TransactionSide.SELL, 5, 150.0, _dt(1)),
        FakeTx(TransactionSide.BUY, 10, 100.0, _dt(10)),
    ]
    result = compute_position("AAPL", txs, current_price=150.0)
    assert result.quantity == 5
    assert result.realized_pnl == 250.0  # (150-100)*5


def test_no_current_price_leaves_market_value_and_unrealized_none():
    txs = [FakeTx(TransactionSide.BUY, 10, 100.0, _dt(5))]
    result = compute_position("AAPL", txs, current_price=None)
    assert result.market_value is None
    assert result.unrealized_pnl is None
