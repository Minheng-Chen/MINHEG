from __future__ import annotations

from typing import Any

from stock_constants import UNAVAILABLE
from stock_utils import clamp, safe_float

POSITIVE = {"beat", "growth", "upgrade", "strong", "profit", "record", "surge", "成長", "上修", "獲利", "合作"}
NEGATIVE = {"miss", "drop", "cut", "downgrade", "weak", "loss", "lawsuit", "probe", "衰退", "下修", "虧損", "訴訟"}
HIGH = {"earnings", "guidance", "fed", "cpi", "lawsuit", "財報", "法說", "利率", "CPI", "FED"}


def _title(item: dict[str, Any]) -> str:
    if not isinstance(item, dict):
        return ""
    if item.get("title"):
        return str(item["title"])
    content = item.get("content")
    return str(content.get("title") or content.get("summary") or "") if isinstance(content, dict) else ""


def analyze_news(news_items: list[dict[str, Any]] | None) -> dict[str, Any]:
    if not news_items:
        return {"status": UNAVAILABLE, "sentiment_score": 0.0, "impact_level": "Low", "risk_level": "Low", "confidence_score": 35.0, "score_for_model": 50.0, "event_types": [], "risk_tags": ["新聞 API 暫時無資料"], "articles": [], "summary": "新聞資料暫時無法取得，以中性處理。"}
    sentiments: list[float] = []; impact = 0; articles: list[dict[str, Any]] = []
    for item in news_items[:8]:
        title = _title(item); text = title.lower()
        pos = sum(1 for w in POSITIVE if w.lower() in text or w in title)
        neg = sum(1 for w in NEGATIVE if w.lower() in text or w in title)
        score = (pos - neg) / max(1, pos + neg)
        sentiments.append(score); articles.append({"title": title or "未命名新聞", "sentiment": score})
        if any(w.lower() in text or w in title for w in HIGH):
            impact += 1
    avg = sum(sentiments) / max(1, len(sentiments))
    impact_level = "High" if impact >= 2 else "Medium" if impact == 1 else "Low"
    risk_level = "High" if avg < -0.45 or (impact_level == "High" and avg < 0) else "Medium" if avg < -0.1 else "Low"
    return {"status": "available", "sentiment_score": safe_float(avg), "impact_level": impact_level, "risk_level": risk_level, "confidence_score": clamp(45 + len(articles) * 5 + impact * 8), "score_for_model": clamp(50 + avg * 35), "event_types": ["產業消息"], "risk_tags": ["重大事件需追蹤"] if impact_level == "High" else ["一般新聞監控"], "articles": articles, "summary": f"新聞情緒分數 {avg:.2f}，事件影響程度為 {impact_level}。"}
