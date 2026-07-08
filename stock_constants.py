MARKET_TAIWAN = "台股"
MARKET_US = "美股"
SUPPORTED_MARKETS = [MARKET_TAIWAN, MARKET_US]
HOLDING_PERIODS = {"1 日": 1, "5 日": 5, "20 日": 20, "60 日": 60}
TRADING_STYLES = ["短線", "波段", "中期"]
UNAVAILABLE = "unavailable"
RISK_LEVELS = [(25, "Low"), (50, "Medium"), (75, "High"), (100, "Extreme")]
STYLE_RISK_MULTIPLIER = {"短線": 0.75, "波段": 1.0, "中期": 1.15}
DECISION_LABELS = {
    "WATCH": "觀望",
    "WAIT_BREAKOUT": "等待突破",
    "WAIT_PULLBACK": "等待回檔",
    "STAGED_ENTRY": "可考慮分批進場",
    "HOLD": "可續抱",
    "REDUCE": "建議減碼",
    "TAKE_PROFIT": "建議停利",
    "STOP_LOSS": "建議停損",
    "AVOID_HIGH_RISK": "避免高風險進場",
}
