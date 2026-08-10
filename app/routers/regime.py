from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import regime_engine
from app.auth import get_current_user
from app.db import get_db
from app.market_data import macro_data

router = APIRouter(prefix="/api/regime", tags=["regime"], dependencies=[Depends(get_current_user)])


@router.get("/macro")
def macro_overview(db: Session = Depends(get_db)):
    """Latest quote + cross-asset relevance table for every tracked macro
    instrument — the Level 2 (macro regime) read for the platform.
    """
    instruments = []
    for key, (_source, symbol, name) in macro_data.MACRO_INSTRUMENTS.items():
        snapshot = regime_engine.latest_macro_snapshot(db, key)
        instruments.append(
            {
                "key": key,
                "symbol": symbol,
                "name": name,
                "price": snapshot.price if snapshot else None,
                "change_pct": snapshot.change_pct if snapshot else None,
                "taken_at": snapshot.taken_at.isoformat() if snapshot else None,
            }
        )
    return {
        "instruments": instruments,
        "nasdaq_cross_asset_relevance": regime_engine.cross_asset_relevance(db, target_key="NASDAQ"),
    }


@router.get("/{symbol}")
def symbol_regime(symbol: str, db: Session = Depends(get_db)):
    """Local regime (trend/momentum/volatility/structure) for `symbol`,
    plus the macro overlay relevant to it. `symbol` accepts an equity
    ticker or a MACRO_INSTRUMENTS key (NASDAQ, SP500, GOLD, DXY, ...).
    """
    report = regime_engine.regime_report(db, symbol)
    if report["local_regime"] is None and not report["cross_asset_relevance"]:
        raise HTTPException(status_code=404, detail="Sem historico suficiente para calcular o regime deste ativo.")
    return report
