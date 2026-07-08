from __future__ import annotations

from typing import Any

from stock_utils import clamp, safe_float


def calculate_scores(technical: dict[str, Any], patterns: dict[str, Any], fundamental: dict[str, Any], news: dict[str, Any], institutional: dict[str, Any], psychology: dict[str, Any], risk: dict[str, Any]) -> dict[str, float]:
    technical_score = safe_float(technical.get("technical_score"), 50)
    pattern_score = safe_float(patterns.get("pattern_score"), 50)
    fundamental_score = safe_float(fundamental.get("score_for_model"), 50)
    news_score = safe_float(news.get("score_for_model"), 50)
    institutional_score = safe_float(institutional.get("score_for_model"), 50)
    psychology_score = safe_float(psychology.get("score_for_model"), 50)
    risk_score = safe_float(risk.get("risk_score"), 50)
    inverse_risk = 100 - risk_score
    trend_score = clamp(technical_score * .34 + pattern_score * .18 + fundamental_score * .12 + news_score * .10 + institutional_score * .10 + psychology_score * .10 + inverse_risk * .06)
    latest = technical.get("latest", {})
    below_ma20 = safe_float(latest.get("close")) < safe_float(latest.get("ma20"))
    below_ma60 = safe_float(latest.get("close")) < safe_float(latest.get("ma60"))
    vr = safe_float(latest.get("volume_ratio"), 1)
    breakout_bonus = 10 if any(p.get("Pattern Name") == "突破壓力" for p in patterns.get("patterns", [])) and vr > 1.5 else 0
    entry_score = clamp(trend_score * .36 + technical_score * .22 + pattern_score * .15 + inverse_risk * .17 + news_score * .06 + institutional_score * .04 + breakout_bonus)
    exit_score = clamp(risk_score * .38 + (100 - technical_score) * .24 + (100 - pattern_score) * .13 + (100 - news_score) * .10 + (100 - institutional_score) * .07 + (10 if below_ma20 and vr > 1.4 else 0) + (12 if below_ma60 else 0))
    available = sum(1 for m in [technical, patterns, fundamental, news, institutional, psychology, risk] if m.get("status") != "unavailable")
    confidence_score = clamp(available / 7 * 65 + (100 - abs(entry_score - (100 - exit_score)) * .45) * .25 + 10)
    return {"technical_score": clamp(technical_score), "fundamental_score": clamp(fundamental_score), "institutional_score": clamp(institutional_score), "market_psychology_score": clamp(psychology_score), "risk_score": clamp(risk_score), "trend_score": trend_score, "entry_score": entry_score, "exit_score": exit_score, "confidence_score": confidence_score}
