from __future__ import annotations

from typing import Any

from stock_constants import MARKET_TAIWAN, UNAVAILABLE


def analyze_institutional(market: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    if payload and payload.get("status") == "available":
        score = float(payload.get("institutional_score", 50))
        return {"status": "available", "institutional_score": score, "score_for_model": score, "direction": payload.get("direction", "中性"), "chip_signal": payload.get("chip_signal", "中性"), "details": payload.get("details", [])}
    details = ["台股三大法人、融資、融券、借券資料已保留串接介面。"] if market == MARKET_TAIWAN else ["美股 Institutional Ownership、Insider Trading、Short Interest、Options Flow 已保留串接介面。"]
    details.append("目前資料不可用時以中性分數處理，不中斷整體分析。")
    return {"status": UNAVAILABLE, "institutional_score": UNAVAILABLE, "score_for_model": 50.0, "direction": "中性", "chip_signal": "中性", "details": details}
