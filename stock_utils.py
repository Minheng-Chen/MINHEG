from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from stock_constants import RISK_LEVELS


def clamp(value: Any, low: float = 0, high: float = 100) -> float:
    try:
        number = float(value)
    except Exception:
        number = low
    if not math.isfinite(number):
        number = low
    return max(low, min(high, number))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except Exception:
        return default
    return number if math.isfinite(number) else default


def format_price(value: Any) -> str:
    number = safe_float(value)
    return f"{number:,.2f}" if abs(number) >= 100 else f"{number:,.4f}".rstrip("0").rstrip(".")


def format_money(value: Any) -> str:
    return f"{safe_float(value):,.0f}"


def format_percent(value: Any, digits: int = 2) -> str:
    return f"{safe_float(value):.{digits}f}%"


def pct_change(current: Any, previous: Any) -> float:
    current_f = safe_float(current, np.nan)
    previous_f = safe_float(previous, np.nan)
    if not math.isfinite(current_f) or not math.isfinite(previous_f) or previous_f == 0:
        return 0.0
    return (current_f - previous_f) / previous_f * 100


def risk_level(score: Any) -> str:
    score_f = clamp(score)
    for threshold, label in RISK_LEVELS:
        if score_f <= threshold:
            return label
    return "Extreme"


def normalize_probability(parts: dict[str, float]) -> dict[str, int]:
    cleaned = {k: max(0.0, safe_float(v)) for k, v in parts.items()}
    total = sum(cleaned.values()) or 1
    raw = {k: v / total * 100 for k, v in cleaned.items()}
    rounded = {k: int(round(v)) for k, v in raw.items()}
    if rounded:
        rounded[max(raw, key=raw.get)] += 100 - sum(rounded.values())
    return rounded


def ensure_ohlcv_columns(data: pd.DataFrame | None) -> pd.DataFrame:
    columns = ["Open", "High", "Low", "Close", "Volume"]
    if data is None or data.empty:
        return pd.DataFrame(columns=columns)
    frame = data.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [c[0] if isinstance(c, tuple) else c for c in frame.columns]
    out = pd.DataFrame(index=frame.index)
    for col in columns:
        out[col] = pd.to_numeric(frame[col], errors="coerce") if col in frame else np.nan
    out = out.dropna(subset=["Close"])
    out["Volume"] = out["Volume"].fillna(0)
    return out


def annualized_volatility(close: pd.Series) -> float:
    returns = close.pct_change().dropna() if close is not None and len(close) else pd.Series(dtype=float)
    return safe_float(returns.std() * np.sqrt(252) * 100) if not returns.empty else 0.0


def drawdown_percent(close: pd.Series) -> float:
    if close is None or close.empty:
        return 0.0
    dd = (close - close.cummax()) / close.cummax().replace(0, np.nan) * 100
    return abs(safe_float(dd.min()))


def fallback_history(seed_symbol: str = "SDE", periods: int = 220) -> pd.DataFrame:
    seed = sum(ord(ch) for ch in seed_symbol) % 997
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=periods)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0006, 0.018, len(dates))))
    high = close * (1 + rng.uniform(0.003, 0.018, len(dates)))
    low = close * (1 - rng.uniform(0.003, 0.018, len(dates)))
    open_price = close * (1 + rng.normal(0, 0.006, len(dates)))
    volume = rng.integers(800_000, 6_000_000, len(dates))
    return pd.DataFrame({"Open": open_price, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates)
