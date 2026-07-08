from __future__ import annotations

from typing import Any

import pandas as pd

from stock_constants import UNAVAILABLE
from stock_utils import clamp, safe_float


def _p(name: str, bias: str, confidence: float, reason: str, failure: str) -> dict[str, Any]:
    return {"Pattern Name": name, "Bullish / Bearish": bias, "Confidence Score": clamp(confidence), "Pattern Reason": reason, "Failure Risk": failure}


def analyze_patterns(history: pd.DataFrame, technical: dict[str, Any]) -> dict[str, Any]:
    if history is None or history.empty or len(history) < 60:
        return {"status": UNAVAILABLE, "pattern_score": 50.0, "patterns": [_p("資料不足", "Neutral", 30, "K 線資料不足。", "型態可信度不足")], "summary": "型態學資料不足。"}
    close, high, low = history["Close"], history["High"], history["Low"]
    latest = safe_float(close.iloc[-1]); recent_high = safe_float(high.iloc[-61:-1].max()); recent_low = safe_float(low.iloc[-61:-1].min())
    vr = safe_float(technical.get("latest", {}).get("volume_ratio"), 1)
    ma20 = safe_float(technical.get("latest", {}).get("ma20")); ma60 = safe_float(technical.get("latest", {}).get("ma60")); ma120 = safe_float(technical.get("latest", {}).get("ma120"))
    patterns: list[dict[str, Any]] = []
    if latest > recent_high and vr > 1.2:
        patterns.append(_p("突破壓力", "Bullish", 75, "價格突破近 60 日壓力且量能提升。", "若跌回突破區，型態失效。"))
    if latest < recent_low and vr > 1.2:
        patterns.append(_p("跌破支撐", "Bearish", 78, "價格跌破近 60 日支撐且量能提升。", "若快速收復支撐，空方型態失效。"))
    if recent_low and (recent_high - recent_low) / recent_low * 100 < 12:
        patterns.append(_p("平台整理", "Neutral", 62, "近 60 日區間收斂。", "需等待突破或跌破確認。"))
    if latest > ma20 > ma60 > ma120 > 0:
        patterns.append(_p("多頭排列", "Bullish", 78, "價格與均線呈多方排序。", "跌破 MA20 且放量時需保守。"))
    elif ma120 > ma60 > ma20 > latest > 0:
        patterns.append(_p("空頭排列", "Bearish", 78, "價格與均線呈空方排序。", "站回 MA20 後風險下降。"))
    if not patterns:
        patterns.append(_p("未出現明確型態", "Neutral", 50, "量價結構尚未形成高信心型態。", "需等待更多 K 線確認。"))
    bull = sum(p["Confidence Score"] for p in patterns if p["Bullish / Bearish"] == "Bullish")
    bear = sum(p["Confidence Score"] for p in patterns if p["Bullish / Bearish"] == "Bearish")
    score = clamp(50 + (bull - bear) / max(1, len(patterns)) * 0.35)
    return {"status": "available", "pattern_score": score, "patterns": patterns, "summary": "；".join(f"{p['Pattern Name']}({p['Bullish / Bearish']})" for p in patterns)}
