from __future__ import annotations

from typing import Any

import pandas as pd

from stock_constants import UNAVAILABLE
from stock_utils import annualized_volatility, clamp, drawdown_percent, risk_level, safe_float


def calculate_risk_score(data: dict[str, Any], technical: dict[str, Any], patterns: dict[str, Any], fundamental: dict[str, Any], news: dict[str, Any], institutional: dict[str, Any]) -> dict[str, Any]:
    history: pd.DataFrame = data.get("history", pd.DataFrame())
    latest = technical.get("latest", {})
    close = safe_float(latest.get("close"), safe_float(data.get("latest", {}).get("price")))
    atr = safe_float(latest.get("atr")); atr_pct = atr / close * 100 if close else 0
    vr = safe_float(latest.get("volume_ratio"), 1); ma20 = safe_float(latest.get("ma20"), close); ma60 = safe_float(latest.get("ma60"), close)
    close_series = history["Close"] if not history.empty else pd.Series(dtype=float)
    components: dict[str, dict[str, Any]] = {}
    components["ATR 波動風險"] = {"score": 20 if atr_pct < 4 else 55 if atr_pct < 7 else 82, "reason": f"ATR 約為價格的 {atr_pct:.2f}%。"}
    vol = annualized_volatility(close_series); components["歷史波動率"] = {"score": clamp(vol / 45 * 55), "reason": f"年化波動率約 {vol:.2f}%。"}
    dd = drawdown_percent(close_series); components["最大回撤"] = {"score": clamp(dd / 18 * 65), "reason": f"近端最大回撤約 {dd:.2f}%。"}
    ma_risk = 20 + (25 if close < ma20 else 0) + (30 if close < ma60 else 0)
    components["關鍵均線風險"] = {"score": clamp(ma_risk), "reason": "跌破主要均線。" if ma_risk > 20 else "價格仍守住主要均線。"}
    volume_risk = 78 if len(history) > 1 and vr > 1.8 and close < safe_float(history["Close"].iloc[-2], close) else 45 if vr > 1.8 else 25
    components["成交量異常風險"] = {"score": volume_risk, "reason": f"Volume Ratio 約 {vr:.2f}。"}
    bearish = [p for p in patterns.get("patterns", []) if p.get("Bullish / Bearish") == "Bearish"]
    components["型態失敗風險"] = {"score": max([safe_float(p.get("Confidence Score")) for p in bearish] or [25]), "reason": "偵測到偏空型態。" if bearish else "未偵測高信心偏空型態。"}
    news_risk = 80 if news.get("risk_level") == "High" else 55 if news.get("risk_level") == "Medium" else 25
    components["新聞事件風險"] = {"score": news_risk, "reason": news.get("summary", "新聞資料暫時無法取得。")}
    components["財報風險"] = {"score": 100 - safe_float(fundamental.get("score_for_model"), 50), "reason": fundamental.get("fundamental_risk", "財報資料暫時無法取得。")}
    components["法人籌碼風險"] = {"score": 100 - safe_float(institutional.get("score_for_model"), 50), "reason": institutional.get("chip_signal", "中性")}
    components["資料來源風險"] = {"score": 57 if data.get("status") == UNAVAILABLE else 45, "reason": "即時資料不可用時，信心需下修。" if data.get("status") == UNAVAILABLE else "資料來源目前可用。"}
    weights = {"ATR 波動風險": .14, "歷史波動率": .10, "最大回撤": .11, "關鍵均線風險": .16, "成交量異常風險": .10, "型態失敗風險": .10, "新聞事件風險": .09, "財報風險": .08, "法人籌碼風險": .07, "資料來源風險": .05}
    score = clamp(sum(components[k]["score"] * w for k, w in weights.items()))
    top = sorted([{"name": k, **v} for k, v in components.items()], key=lambda x: x["score"], reverse=True)[:5]
    level = risk_level(score)
    suggestion = "風險偏高，建議縮小投入比例並使用嚴格停損。" if level in {"High", "Extreme"} else "需確認進場條件與停損價格。" if level == "Medium" else "風險相對較低，但仍需依停損控管。"
    return {"status": "available", "risk_score": score, "risk_level": level, "components": components, "top_risk_sources": top, "risk_control_suggestion": suggestion, "atr_percent": atr_pct, "volatility_percent": vol, "max_drawdown_percent": dd}
