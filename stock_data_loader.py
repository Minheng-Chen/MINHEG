from __future__ import annotations

from typing import Any

import pandas as pd

from stock_constants import UNAVAILABLE
from stock_utils import ensure_ohlcv_columns, fallback_history, pct_change, safe_float

try:
    import yfinance as yf
except Exception:
    yf = None


def _info(ticker: Any) -> dict[str, Any]:
    try:
        value = ticker.get_info()
        return value if isinstance(value, dict) else {}
    except Exception:
        try:
            return ticker.info if isinstance(ticker.info, dict) else {}
        except Exception:
            return {}


def _snapshot(history: pd.DataFrame, info: dict[str, Any]) -> dict[str, Any]:
    close = history["Close"].dropna()
    latest = safe_float(close.iloc[-1]) if len(close) else 0.0
    previous = safe_float(close.iloc[-2], latest) if len(close) > 1 else latest
    week = safe_float(close.iloc[-6], previous) if len(close) > 6 else previous
    month = safe_float(close.iloc[-22], previous) if len(close) > 22 else previous
    return {
        "price": latest,
        "previous_close": previous,
        "daily_change_pct": pct_change(latest, previous),
        "weekly_change_pct": pct_change(latest, week),
        "monthly_change_pct": pct_change(latest, month),
        "week_52_high": safe_float(close.tail(252).max(), latest),
        "week_52_low": safe_float(close.tail(252).min(), latest),
        "volume": int(safe_float(history["Volume"].iloc[-1])) if len(history) else 0,
        "currency": info.get("currency", ""),
    }


def load_stock_data(market: str, symbol: str, holding_days: int) -> dict[str, Any]:
    errors: list[str] = []
    info: dict[str, Any] = {}
    news: list[dict[str, Any]] = []
    history = pd.DataFrame()
    if yf is not None:
        try:
            ticker = yf.Ticker(symbol)
            period = "6mo" if holding_days <= 5 else "1y" if holding_days <= 20 else "2y"
            history = ensure_ohlcv_columns(ticker.history(period=period, interval="1d", auto_adjust=False))
            info = _info(ticker)
            try:
                news = ticker.news[:8] if isinstance(ticker.news, list) else []
            except Exception:
                news = []
        except Exception as exc:
            errors.append(f"資料來源讀取失敗：{exc}")
    status = "available"
    source = "Yahoo Finance via yfinance"
    if history.empty:
        status = UNAVAILABLE
        source = UNAVAILABLE
        history = fallback_history(symbol)
        errors.append("即時行情暫時無法取得，Dashboard 使用安全示範序列維持分析流程。")
    company = {
        "status": "available" if info else UNAVAILABLE,
        "name": info.get("shortName") or info.get("longName") or symbol,
        "sector": info.get("sector", UNAVAILABLE),
        "industry": info.get("industry", UNAVAILABLE),
        "currency": info.get("currency", ""),
        "exchange": info.get("exchange", market),
    }
    fundamentals = {"status": "available" if info else UNAVAILABLE, **{k: info.get(k) for k in ["revenueGrowth", "grossMargins", "operatingMargins", "trailingEps", "earningsQuarterlyGrowth", "returnOnEquity", "returnOnAssets", "debtToEquity", "freeCashflow", "trailingPE", "priceToBook", "pegRatio"]}}
    return {"market": market, "symbol": symbol, "status": status, "source": source, "history": history, "latest": _snapshot(history, info), "company": company, "fundamentals": fundamentals, "news": news, "institutional": {"status": UNAVAILABLE}, "errors": errors}
