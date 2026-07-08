from __future__ import annotations

from typing import Any

from stock_constants import DECISION_LABELS
from stock_utils import clamp, safe_float
from stock_validation import StockInput


def make_final_decision(stock_input: StockInput, technical: dict[str, Any], patterns: dict[str, Any], risk: dict[str, Any], trend: dict[str, Any], scores: dict[str, float], news: dict[str, Any], institutional: dict[str, Any]) -> dict[str, Any]:
    risk_score = clamp(scores.get("risk_score", risk.get("risk_score", 50))); trend_score = clamp(scores.get("trend_score", trend.get("trend_score", 50)))
    entry_score = clamp(scores.get("entry_score", 50)); exit_score = clamp(scores.get("exit_score", 50)); confidence = clamp(scores.get("confidence_score", 50))
    latest = technical.get("latest", {}); close = safe_float(latest.get("close")); ma20 = safe_float(latest.get("ma20")); ma60 = safe_float(latest.get("ma60")); vr = safe_float(latest.get("volume_ratio"), 1)
    reasons: list[str] = []; risks: list[str] = []; conditions: list[str] = []; not_ok: list[str] = []
    decision = DECISION_LABELS["WATCH"]
    if risk_score > 75:
        decision = DECISION_LABELS["AVOID_HIGH_RISK"]; reasons.append("Risk Score 高於 75，風險等級過高。")
    elif exit_score > 70:
        decision = DECISION_LABELS["REDUCE"]; reasons.append("Exit Score 高於 70，退場或減碼訊號較強。")
    elif risk_score > 60 and entry_score < 70:
        decision = DECISION_LABELS["WATCH"]; reasons.append("風險偏高且進場分數不足。")
    elif trend_score > 70 and entry_score > 70 and risk_score < 60:
        decision = DECISION_LABELS["STAGED_ENTRY"] if stock_input.allow_staged_entry else DECISION_LABELS["WAIT_PULLBACK"]; reasons.append("趨勢與進場分數較佳，且風險低於 60。")
    elif trend_score > 60 and entry_score > 60 and risk_score < 65:
        decision = DECISION_LABELS["WAIT_PULLBACK"]; reasons.append("條件偏正向，但尚未達高信心門檻。")
    elif any(p.get("Pattern Name") == "突破壓力" for p in patterns.get("patterns", [])):
        decision = DECISION_LABELS["WAIT_BREAKOUT"]; reasons.append("偵測到壓力突破訊號，需確認量能延續。")
    else:
        reasons.append("多因子分數未形成明確優勢，暫以觀望處理。")
    if close < ma20 and vr > 1.4: risks.append("跌破 MA20 且成交量放大，退場風險提高。")
    if close < ma60: risks.append("跌破 MA60，風險分數需保守看待。")
    top = [f"{x['name']}：{x['reason']}" for x in risk.get("top_risk_sources", [])[:3]]
    conditions.append("需同時符合使用者風險承受度、停損規則與情境條件。")
    not_ok.append("若重大事件未消化、資料來源 unavailable，或價格跌破停損條件，則不適用積極策略。")
    return {"final_decision": decision, "trend_score": trend_score, "risk_score": risk_score, "entry_score": entry_score, "exit_score": exit_score, "confidence_score": confidence, "main_reasons": reasons, "risk_explanation": top + risks, "applicable_conditions": conditions, "not_applicable_scenarios": not_ok}
