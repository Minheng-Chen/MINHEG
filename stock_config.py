import os

APP_NAME = "Stock Decision Engine（SDE）"
APP_TAGLINE = "台股與美股多因子交易決策輔助平台"
DEFAULT_CAPITAL = 100_000
DEFAULT_MAX_LOSS_PERCENT = 8.0
DEFAULT_TRADING_STYLE = "波段"


def get_secret(name: str, default: str = "") -> str:
    try:
        import streamlit as st
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)
