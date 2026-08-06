from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.audit import audit
from app.backtest import backtest_conditions
from app.db import get_db
from app.market_data import yfinance_client
from app.models import AlertCondition, AlertRule, User, WatchlistItem
from app.rules_engine import RuleContext
from app.saas import ensure_limit, get_or_create_workspace
from app.schemas import (
    AlertRuleCreate,
    AlertRuleOut,
    BacktestRequest,
    BacktestResponse,
    WatchlistItemCreate,
    WatchlistItemOut,
)

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[WatchlistItemOut])
def list_watchlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    workspace = get_or_create_workspace(db, user)
    return (
        db.query(WatchlistItem)
        .filter(WatchlistItem.active.is_(True))
        .filter((WatchlistItem.workspace_id == workspace.id) | (WatchlistItem.workspace_id.is_(None)))
        .all()
    )


@router.post("", response_model=WatchlistItemOut, status_code=201)
def create_watchlist_item(payload: WatchlistItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    symbol = payload.symbol.upper().strip()
    workspace = get_or_create_workspace(db, user)
    existing = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.symbol == symbol)
        .filter((WatchlistItem.workspace_id == workspace.id) | (WatchlistItem.workspace_id.is_(None)))
        .first()
    )
    if existing:
        existing.active = True
        existing.user_id = existing.user_id or getattr(user, "id", None)
        existing.workspace_id = existing.workspace_id or workspace.id
        existing.label = payload.label or existing.label
        audit(db, user, "watchlist.reactivate", "watchlist_item", existing.id, {"symbol": symbol})
        db.commit()
        db.refresh(existing)
        return existing

    ensure_limit(db, workspace, "watchlist_items")
    item = WatchlistItem(symbol=symbol, label=payload.label, user_id=getattr(user, "id", None), workspace_id=workspace.id)
    db.add(item)
    audit(db, user, "watchlist.create", "watchlist_item", symbol, {"symbol": symbol})
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def deactivate_watchlist_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(WatchlistItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    workspace = get_or_create_workspace(db, user)
    if item.workspace_id not in (None, workspace.id):
        raise HTTPException(status_code=404, detail="Ativo nao encontrado")
    item.active = False
    audit(db, user, "watchlist.deactivate", "watchlist_item", item.id, {"symbol": item.symbol})
    db.commit()


@router.post("/{item_id}/rules", response_model=AlertRuleOut, status_code=201)
def create_rule(item_id: int, payload: AlertRuleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(WatchlistItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    if not payload.conditions:
        raise HTTPException(status_code=400, detail="A regra precisa de pelo menos uma condição")

    workspace = get_or_create_workspace(db, user)
    if item.workspace_id not in (None, workspace.id):
        raise HTTPException(status_code=404, detail="Ativo nao encontrado")
    ensure_limit(db, workspace, "alert_rules")
    rule = AlertRule(watchlist_item_id=item_id, logic=payload.logic, cooldown_minutes=payload.cooldown_minutes)
    rule.conditions = [
        AlertCondition(
            rule_type=cond.rule_type,
            threshold=cond.threshold,
            param_a=cond.param_a,
            param_b=cond.param_b,
        )
        for cond in payload.conditions
    ]
    db.add(rule)
    audit(db, user, "rule.create", "alert_rule", item_id, {"symbol": item.symbol})
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/{item_id}/rules", response_model=list[AlertRuleOut])
def list_rules(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(WatchlistItem).filter(WatchlistItem.id == item_id, WatchlistItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    return db.query(AlertRule).filter(AlertRule.watchlist_item_id == item_id).all()


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rule = (
        db.query(AlertRule)
        .join(WatchlistItem, AlertRule.watchlist_item_id == WatchlistItem.id)
        .filter(AlertRule.id == rule_id, WatchlistItem.user_id == user.id)
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    rule.active = False
    db.commit()


@router.post("/rules/backtest", response_model=BacktestResponse)
def backtest_rule(payload: BacktestRequest):
    history = yfinance_client.get_history(
        payload.symbol.upper(), period=payload.period, interval=payload.interval
    )
    if history.empty:
        raise HTTPException(status_code=404, detail="Sem dados históricos para este símbolo")

    conditions = [
        RuleContext(rule_type=c.rule_type, threshold=c.threshold, param_a=c.param_a, param_b=c.param_b)
        for c in payload.conditions
    ]
    result = backtest_conditions(
        conditions, payload.logic, history, symbol=payload.symbol.upper(), forward_bars=payload.forward_bars
    )
    return result
