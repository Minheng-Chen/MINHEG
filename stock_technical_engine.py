from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from stock_constants import UNAVAILABLE
from stock_utils import clamp, safe_float


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    prev = close.shift(1)
    tr = pd.concat([high - low, (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(window).mean()


def calculate_technical_indicators(history: pd.DataFrame) -> pd.DataFrame:
    frame = history.copy()
    close, high, low, volume = frame["Close"], frame["High"], frame["Low"], frame["Volume"]
    for window in [5, 10, 20, 60, 120]:
        frame[f"MA{window}"] = close.rolling(window).mean()
    frame["EMA"] = close.ewm(span=20, adjust=False).mean()
    ema12, ema26 = close.ewm(span=12, adjust=False).mean(), close.ewm(span=26, adjust=False).mean()
    frame["MACD"] = ema12 - ema26
    frame["MACD_SIGNAL"] = frame["MACD"].ewm(span=9, adjust=False).mean()
    frame["MACD_HIST"] = frame["MACD"] - frame["MACD_SIGNAL"]
    frame["RSI"] = _rsi(close)
    low9, high9 = low.rolling(9).min(), high.rolling(9).max()
    frame["K"] = ((close - low9) / (high9 - low9).replace(0, np.nan) * 100).ewm(com=2, adjust=False).mean()
    frame["D"] = frame["K"].ewm(com=2, adjust=False).mean()
    frame["ATR"] = _atr(high, low, close)
    mid = close.rolling(20).mean(); std = close.rolling(20).std()
    frame["BB_MIDDLE"], frame["BB_UPPER"], frame["BB_LOWER"] = mid, mid + 2 * std, mid - 2 * std
    tp = (high + low + close) / 3
    frame["VWAP"] = (tp * volume).cumsum() / volume.replace(0, np.nan).cumsum()
    frame["OBV"] = (np.sign(close.diff()).fillna(0) * volume).cumsum()
    frame["ADX"] = (abs(close.diff()).rolling(14).mean() / frame["ATR"].replace(0, np.nan) * 100).clip(0, 100)
    frame["VOLUME_RATIO"] = volume / volume.rolling(20).mean().replace(0, np.nan)
    return frame


def analyze_technical(history: pd.DataFrame) -> dict[str, Any]:
    if history is None or history.empty or len(history) < 30:
        return {"status": UNAVAILABLE, "technical_score": 50.0, "indicators": pd.DataFrame(), "bullish_signals": [], "bearish_signals": ["技術指標計算資料不足。"], "explanation": "資料不足，技術分數以中性處理。"}
    indicators = calculate_technical_indicators(history)
    latest = indicators.iloc[-1]
    previous = indicators.iloc[-2]
    close = safe_float(latest["Close"]); ma20 = safe_float(latest.get("MA20")); ma60 = safe_float(latest.get("MA60")); ma120 = safe_float(latest.get("MA120"))
    rsi = safe_float(latest.get("RSI"), 50); macd_hist = safe_float(latest.get("MACD_HIST")); vr = safe_float(latest.get("VOLUME_RATIO"), 1); adx = safe_float(latest.get("ADX")); atr = safe_float(latest.get("ATR"))
    score = 50.0; bullish: list[str] = []; bearish: list[str] = []
    if close > ma20 > 0: score += 8; bullish.append("收盤價站上 MA20，短中期趨勢偏強。")
    else: score -= 8; bearish.append("收盤價未站上 MA20，短中期動能仍需觀察。")
    if ma20 > ma60 > 0: score += 10; bullish.append("MA20 高於 MA60，趨勢結構偏多。")
    elif ma60 > 0: score -= 10; bearish.append("MA20 低於 MA60，趨勢結構偏弱。")
    if 45 <= rsi <= 70: score += 6; bullish.append("RSI 位於健康動能區間。")
    elif rsi > 75: score -= 5; bearish.append("RSI 偏高，追價風險上升。")
    elif rsi < 35: score -= 4; bearish.append("RSI 偏低，動能不足。")
    if macd_hist > 0: score += 7; bullish.append("MACD 柱狀體為正。")
    else: score -= 6; bearish.append("MACD 柱狀體為負。")
    if vr > 1.5 and close > safe_float(previous["Close"]): score += 7; bullish.append("放量上漲，進場動能提升。")
    if vr > 1.5 and close < safe_float(previous["Close"]): score -= 9; bearish.append("放量下跌，退場風險提高。")
    return {"status": "available", "technical_score": clamp(score), "indicators": indicators, "bullish_signals": bullish, "bearish_signals": bearish, "explanation": "；".join((bullish + bearish)[:5]) or "技術面偏中性。", "latest": {"close": close, "ma20": ma20, "ma60": ma60, "ma120": ma120, "rsi": rsi, "macd_hist": macd_hist, "atr": atr, "volume_ratio": vr, "adx": adx}}
