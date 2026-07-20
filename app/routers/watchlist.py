from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_login_api
from app.db import get_db
from app.models import AlertRule, WatchlistItem
from app.schemas import AlertRuleCreate, AlertRuleOut, WatchlistItemCreate, WatchlistItemOut

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"], dependencies=[Depends(require_login_api)])


@router.get("", response_model=list[WatchlistItemOut])
def list_watchlist(db: Session = Depends(get_db)):
    return db.query(WatchlistItem).filter(WatchlistItem.active.is_(True)).all()


@router.post("", response_model=WatchlistItemOut, status_code=201)
def create_watchlist_item(payload: WatchlistItemCreate, db: Session = Depends(get_db)):
    symbol = payload.symbol.upper().strip()
    existing = db.query(WatchlistItem).filter(WatchlistItem.symbol == symbol).first()
    if existing:
        existing.active = True
        existing.label = payload.label or existing.label
        db.commit()
        db.refresh(existing)
        return existing

    item = WatchlistItem(symbol=symbol, label=payload.label)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def deactivate_watchlist_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(WatchlistItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    item.active = False
    db.commit()


@router.post("/{item_id}/rules", response_model=AlertRuleOut, status_code=201)
def create_rule(item_id: int, payload: AlertRuleCreate, db: Session = Depends(get_db)):
    item = db.get(WatchlistItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    rule = AlertRule(
        watchlist_item_id=item_id,
        rule_type=payload.rule_type,
        threshold=payload.threshold,
        param_a=payload.param_a,
        param_b=payload.param_b,
        cooldown_minutes=payload.cooldown_minutes,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/{item_id}/rules", response_model=list[AlertRuleOut])
def list_rules(item_id: int, db: Session = Depends(get_db)):
    return db.query(AlertRule).filter(AlertRule.watchlist_item_id == item_id).all()


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    rule.active = False
    db.commit()
