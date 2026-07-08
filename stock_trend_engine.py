from __future__ import annotations

from typing import Any

from stock_utils import clamp, normalize_probability, safe_float


def build_trend_scenarios(technical: dict[str, Any], patterns: dict[str, Any], risk: dict[str, Any], scores: dict[str, float], holding_days: int) -> dict[str, Any]:
    trend_score = clamp(scores.get("trend_score", 50)); risk_score = clamp(risk.get("risk_score", 50))
    latest = technical.get("latest", {}); close = safe_float(latest.get("close")); atr = safe_float(latest.get("atr")); atr_pct = atr / close * 100 if close else 2
    factor = max(1.0, (holding_days / 20) ** 0.5)
    probs = normalize_probability({"Bull Case": max(10, trend_score * .75 + (100 - risk_score) * .25), "Base Case": max(20, 100 - abs(trend_score - 50) * .6 - abs(risk_score - 50) * .35), "Bear Case": max(10, risk_score * .7 + (100 - trend_score) * .3)})
    bull = max(1.5, atr_pct * 1.35 * factor + max(0, trend_score - 55) * .08)
    base = (trend_score - 50) * .06 * factor
    bear = -max(1.2, atr_pct * 1.15 * factor + max(0, risk_score - 55) * .07)
    bullish = [p["Pattern Name"] for p in patterns.get("patterns", []) if p.get("Bullish / Bearish") == "Bullish"]
    bearish = [p["Pattern Name"] for p in patterns.get("patterns", []) if p.get("Bullish / Bearish") == "Bearish"]
    return {"status": "available", "trend_score": trend_score, "probability_sum": sum(probs.values()), "scenarios": {"Bull Case": {"estimated_return_pct": round(bull, 2), "probability": probs["Bull Case"], "support_factors": bullish[:3] or ["技術分數與量價結構偏多時才成立。"], "invalidation": "跌破 MA20 並伴隨放量，或風險分數升高到 High 以上。"}, "Base Case": {"estimated_return_pct": round(base, 2), "probability": probs["Base Case"], "support_factors": ["價格維持主要區間內震盪，量能未出現極端變化。"], "invalidation": "突破或跌破整理區間且量能明顯放大。"}, "Bear Case": {"estimated_return_pct": round(bear, 2), "probability": probs["Bear Case"], "support_factors": bearish[:3] or ["跌破關鍵均線、波動率擴大或事件風險升高時成立。"], "invalidation": "重新站回關鍵均線且風險分數下降。"}}}
