from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.copilot import analyze_symbol
from app.db import get_db
from app.schemas import CopilotAnalyzeRequest

router = APIRouter(prefix="/api/copilot", tags=["copilot"], dependencies=[Depends(get_current_user)])


@router.post("/analyze")
def analyze(payload: CopilotAnalyzeRequest, db: Session = Depends(get_db)):
    return analyze_symbol(
        db,
        symbol=payload.symbol,
        capital_usd=payload.capital_usd,
        risk_budget_pct=payload.risk_budget_pct,
        question=payload.question,
    )
