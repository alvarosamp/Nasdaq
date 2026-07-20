from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import PriceSnapshot, Transaction, WatchlistItem
from app.positions import compute_position
from app.schemas import PositionSummaryOut, TransactionCreate, TransactionOut

router = APIRouter(prefix="/api/positions", tags=["positions"], dependencies=[Depends(get_current_user)])


def _latest_price(db: Session, symbol: str) -> float | None:
    item = db.query(WatchlistItem).filter(WatchlistItem.symbol == symbol).first()
    if item is None:
        return None
    snap = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.watchlist_item_id == item.id)
        .order_by(PriceSnapshot.taken_at.desc())
        .first()
    )
    return snap.price if snap else None


@router.get("", response_model=list[PositionSummaryOut])
def list_positions(db: Session = Depends(get_db)):
    symbols = [s for (s,) in db.query(Transaction.symbol).distinct().all()]
    summaries = []
    for symbol in symbols:
        transactions = db.query(Transaction).filter(Transaction.symbol == symbol).all()
        current_price = _latest_price(db, symbol)
        summary = compute_position(symbol, transactions, current_price)
        summaries.append(summary)
    return summaries


@router.post("/transactions", response_model=TransactionOut, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    tx = Transaction(
        symbol=payload.symbol.upper().strip(),
        side=payload.side,
        quantity=payload.quantity,
        price=payload.price,
        executed_at=payload.executed_at,
        notes=payload.notes,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/{symbol}/transactions", response_model=list[TransactionOut])
def list_transactions(symbol: str, db: Session = Depends(get_db)):
    return (
        db.query(Transaction)
        .filter(Transaction.symbol == symbol.upper())
        .order_by(Transaction.executed_at.desc())
        .all()
    )


@router.delete("/transactions/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    db.delete(tx)
    db.commit()
