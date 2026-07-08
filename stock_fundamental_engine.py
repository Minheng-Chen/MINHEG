from __future__ import annotations

from typing import Any

from stock_constants import UNAVAILABLE
from stock_utils import clamp, safe_float


def _pct(value: Any) -> float | str:
    if value is None:
        return UNAVAILABLE
    number = safe_float(value)
    return number * 100 if abs(number) <= 1.5 else number


def analyze_fundamentals(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data or data.get("status") == UNAVAILABLE:
        return {"status": UNAVAILABLE, "fundamental_score": UNAVAILABLE, "score_for_model": 50.0, "fundamental_risk": "財報資料暫時無法取得", "support_factors": [], "risk_factors": ["財報資料缺失，信心分數需保守。"], "metrics": {}}
    metrics = {
        "Revenue Growth": _pct(data.get("revenueGrowth")),
        "Gross Margin": _pct(data.get("grossMargins")),
        "Operating Margin": _pct(data.get("operatingMargins")),
        "EPS": data.get("trailingEps", UNAVAILABLE),
        "EPS Growth": _pct(data.get("earningsQuarterlyGrowth")),
        "ROE": _pct(data.get("returnOnEquity")),
        "ROA": _pct(data.get("returnOnAssets")),
        "Debt Ratio": data.get("debtToEquity", UNAVAILABLE),
        "Free Cash Flow": data.get("freeCashflow", UNAVAILABLE),
        "PER": data.get("trailingPE", UNAVAILABLE),
        "PBR": data.get("priceToBook", UNAVAILABLE),
        "PEG": data.get("pegRatio", UNAVAILABLE),
    }
    score = 50.0; support: list[str] = []; risks: list[str] = []
    if safe_float(metrics["Revenue Growth"]) > 10: score += 10; support.append("營收成長具支撐。")
    elif safe_float(metrics["Revenue Growth"]) < -5: score -= 10; risks.append("營收成長偏弱。")
    if safe_float(metrics["Operating Margin"]) > 10: score += 8; support.append("營業利益率具支撐。")
    elif safe_float(metrics["Operating Margin"]) < 5: score -= 8; risks.append("營業利益率偏低。")
    if safe_float(metrics["EPS"]) > 0: score += 7; support.append("EPS 為正。")
    else: score -= 7; risks.append("EPS 非正值或缺失。")
    if safe_float(metrics["ROE"]) > 12: score += 7; support.append("ROE 具資本效率支撐。")
    if safe_float(metrics["Debt Ratio"]) > 180: score -= 8; risks.append("槓桿或負債偏高。")
    final = clamp(score)
    return {"status": "available", "fundamental_score": final, "score_for_model": final, "fundamental_risk": "Low" if final >= 70 else "Medium" if final >= 45 else "High", "support_factors": support or ["財報訊號偏中性。"], "risk_factors": risks or ["未偵測明確財報惡化訊號。"], "metrics": metrics}
