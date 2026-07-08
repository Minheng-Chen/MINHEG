from __future__ import annotations

from dataclasses import dataclass
import re

from stock_constants import HOLDING_PERIODS, MARKET_TAIWAN, MARKET_US, SUPPORTED_MARKETS, TRADING_STYLES
from stock_utils import safe_float


@dataclass
class StockInput:
    market: str
    raw_symbol: str
    symbol: str
    capital: float
    holding_label: str
    holding_days: int
    max_loss_percent: float
    trading_style: str
    allow_staged_entry: bool
    use_trailing_stop: bool


@dataclass
class ValidationResult:
    ok: bool
    input_data: StockInput | None
    errors: list[str]
    warnings: list[str]


def normalize_symbol(market: str, raw_symbol: str) -> tuple[str, list[str]]:
    symbol = re.sub(r"\s+", "", str(raw_symbol or "")).upper()
    warnings: list[str] = []
    if market == MARKET_TAIWAN:
        if re.fullmatch(r"\d{4,6}", symbol):
            symbol = f"{symbol}.TW"
            warnings.append("台股純數字代號已自動轉為 .TW；上櫃股票請輸入 .TWO。")
        elif not (symbol.endswith(".TW") or symbol.endswith(".TWO")):
            warnings.append("台股建議使用 2330、2330.TW 或 8069.TWO。")
    elif market == MARKET_US:
        symbol = symbol.replace(".", "-")
    return symbol, warnings


def validate_user_inputs(market: str, symbol: str, capital: float, holding_label: str, max_loss_percent: float, trading_style: str, allow_staged_entry: bool, use_trailing_stop: bool) -> ValidationResult:
    errors: list[str] = []
    normalized, warnings = normalize_symbol(market, symbol)
    if market not in SUPPORTED_MARKETS:
        errors.append("市場選擇不正確。")
    if not normalized:
        errors.append("請輸入股票代號。")
    if market == MARKET_TAIWAN and not re.fullmatch(r"\d{4,6}(\.(TW|TWO))?", normalized):
        errors.append("台股代號格式需為 2330、2330.TW 或 8069.TWO。")
    if market == MARKET_US and not re.fullmatch(r"[A-Z][A-Z0-9-]{0,9}", normalized):
        errors.append("美股代號格式不正確。")
    capital_f = safe_float(capital)
    if capital_f <= 0:
        errors.append("投入資金需大於 0。")
    if holding_label not in HOLDING_PERIODS:
        errors.append("持有期間不正確。")
    loss_f = safe_float(max_loss_percent)
    if loss_f <= 0 or loss_f > 80:
        errors.append("最大可承受虧損比例需介於 0 到 80。")
    if trading_style not in TRADING_STYLES:
        errors.append("交易風格不正確。")
    input_data = None if errors else StockInput(market, symbol, normalized, capital_f, holding_label, HOLDING_PERIODS[holding_label], loss_f, trading_style, allow_staged_entry, use_trailing_stop)
    return ValidationResult(not errors, input_data, errors, warnings)
