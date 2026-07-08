from __future__ import annotations

from typing import Any

import pandas as pd

from stock_utils import clamp, safe_float


def analyze_market_psychology(history: pd.DataFrame, technical: dict[str, Any], patterns: dict[str, Any], news: dict[str, Any], institutional: dict[str, Any]) -> dict[str, Any]:
    latest = technical.get("latest", {})
    rsi = safe_float(latest.get("rsi"), 50); vr = safe_float(latest.get("volume_ratio"), 1)
    atr = safe_float(latest.get("atr")); close = safe_float(latest.get("close")); atr_pct = atr / close * 100 if close else 0
    sentiment = safe_float(news.get("sentiment_score")); pattern_score = safe_float(patterns.get("pattern_score"), 50)
    institutional_score = safe_float(institutional.get("score_for_model"), 50)
    score = 50.0; label = "中性"; reasons: list[str] = []
    if rsi > 75 and vr > 1.4:
        score += 22; label = "過熱"; reasons.append("RSI 偏高且量能放大，追價情緒升高。")
    elif rsi < 30 and atr_pct > 4:
        score -= 22; label = "恐慌"; reasons.append("RSI 偏低且波動擴大，恐慌賣壓需留意。")
    if pattern_score > 65 and sentiment >= 0:
        score += 10; label = label if label != "中性" else "追價"; reasons.append("型態偏多且新聞未顯示負面壓力。")
    elif pattern_score < 40:
        score -= 10; label = label if label != "中性" else "殺低"; reasons.append("型態偏弱，市場心理偏防守。")
    if institutional_score > 62:
        score += 8; label = label if label != "中性" else "吸籌"; reasons.append("籌碼面分數偏高。")
    elif institutional_score < 38:
        score -= 8; label = label if label != "中性" else "出貨"; reasons.append("籌碼面分數偏低。")
    if sentiment < -0.4:
        score -= 12; reasons.append("新聞情緒偏負面。")
    elif sentiment > 0.4:
        score += 8; reasons.append("新聞情緒偏正面。")
    return {"status": "available", "market_psychology_score": clamp(score), "score_for_model": clamp(score), "market_psychology_label": label, "reason": "；".join(reasons) or "未顯示極端心理訊號。"}
