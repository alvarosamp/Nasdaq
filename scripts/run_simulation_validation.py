from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app import paper_simulator
from app.market_data import yfinance_client


SYMBOLS = ["AAPL", "MSFT", "NVDA", "SNAP"]
REPORT_PATH = Path(os.getenv("SIM_VALIDATION_REPORT", "/app/data/simulation_validation_report.json"))


def _market_data_check(symbols: list[str]) -> list[dict]:
    rows = []
    for symbol in symbols:
        history = yfinance_client.get_history(symbol, period="1y", interval="1d")
        rows.append(
            {
                "symbol": symbol,
                "rows": int(len(history)),
                "has_ohlcv": bool(
                    not history.empty
                    and {"open", "high", "low", "close", "volume"}.issubset(set(history.columns))
                    and history[["open", "high", "low", "close", "volume"]].dropna().shape[0] >= 90
                ),
                "last_close": None if history.empty else round(float(history["close"].dropna().iloc[-1]), 2),
            }
        )
    return rows


def build_report(symbols: list[str] | None = None) -> dict:
    symbols = symbols or SYMBOLS
    selected_filter, calibration, prepared = paper_simulator.calibrate(symbols)
    state = paper_simulator._load_state()
    portfolio_value = paper_simulator._portfolio_value(state, prepared)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "symbols": symbols,
        "initial_capital": float(state.get("initial_capital", 200.0)),
        "cash": float(state.get("cash", 0.0)),
        "open_positions": state.get("positions", {}),
        "closed_trades": state.get("closed_trades", []),
        "portfolio_value": portfolio_value,
        "market_data": _market_data_check(symbols),
        "calibration": calibration,
        "can_trade_now": selected_filter is not None,
        "decision_rule": "Opera somente se precisao historica >= 58%, retorno medio futuro > 0 e sinal atual passar no filtro.",
        "risk_rule": "Compra no maximo uma posicao, usa a banca disponivel, stop em 1 ATR e alvo em 2 ATR.",
    }


def main() -> None:
    report = build_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
