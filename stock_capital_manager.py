from __future__ import annotations

from typing import Any

from stock_constants import STYLE_RISK_MULTIPLIER
from stock_utils import clamp, safe_float
from stock_validation import StockInput


def _allocation(risk_score: float) -> float:
    if risk_score <= 25: return .75
    if risk_score <= 50: return .55
    if risk_score <= 75: return .35
    return .15


def calculate_capital_plan(stock_input: StockInput, latest_price: float, technical: dict[str, Any], risk: dict[str, Any], trend: dict[str, Any], news: dict[str, Any]) -> dict[str, Any]:
    capital = stock_input.capital; price = safe_float(latest_price); risk_score = safe_float(risk.get("risk_score"), 50)
    atr = safe_float(technical.get("latest", {}).get("atr")); atr_pct = atr / price * 100 if price else 0
    allocation = _allocation(risk_score) * STYLE_RISK_MULTIPLIER.get(stock_input.trading_style, 1.0)
    if news.get("impact_level") == "High" and safe_float(news.get("sentiment_score")) < -0.5: allocation *= .75
    if atr_pct > 7: allocation *= .70
    elif atr_pct > 4: allocation *= .85
    allocation = clamp(allocation * 100, 5, 80) / 100
    position = capital * allocation
    first, second, third = (position * .4, position * .35, position * .25) if stock_input.allow_staged_entry else (position, 0.0, 0.0)
    stop_pct = min(stock_input.max_loss_percent, max(atr_pct * 1.8, 2.0)); take_pct = max(stop_pct * 1.6, atr_pct * 2.4, 3.0)
    scenarios = trend.get("scenarios", {})
    bull = safe_float(scenarios.get("Bull Case", {}).get("estimated_return_pct")); base = safe_float(scenarios.get("Base Case", {}).get("estimated_return_pct")); bear = safe_float(scenarios.get("Bear Case", {}).get("estimated_return_pct"))
    return {"suggested_allocation_pct": allocation * 100, "position_amount": position, "first_entry_amount": first, "second_entry_amount": second, "third_entry_amount": third, "reserve_cash": capital - position, "stop_loss_price": price * (1 - stop_pct / 100) if price else 0, "take_profit_price": price * (1 + take_pct / 100) if price else 0, "trailing_stop_price": max(0, price - atr * 2) if stock_input.use_trailing_stop and price else 0, "estimated_max_loss_amount": position * stop_pct / 100, "bull_case_profit": position * bull / 100, "base_case_profit": position * base / 100, "bear_case_loss": position * bear / 100, "return_rate_percent": {"Bull Case": bull, "Base Case": base, "Bear Case": bear}, "risk_adjustment_reason": "風險越高，建議投入比例越低；ATR 或負面高影響新聞會再下修比例。"}
