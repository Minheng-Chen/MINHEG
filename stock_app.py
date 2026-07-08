from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from stock_capital_manager import calculate_capital_plan
from stock_chart_builder import build_candlestick_chart, build_risk_radar_chart, build_scenario_chart, build_score_gauge, build_technical_indicator_chart, build_volume_chart
from stock_config import APP_NAME, APP_TAGLINE, DEFAULT_CAPITAL, DEFAULT_MAX_LOSS_PERCENT, DEFAULT_TRADING_STYLE
from stock_constants import HOLDING_PERIODS, MARKET_TAIWAN, MARKET_US, TRADING_STYLES, UNAVAILABLE
from stock_data_loader import load_stock_data
from stock_decision_engine import make_final_decision
from stock_fundamental_engine import analyze_fundamentals
from stock_institutional_engine import analyze_institutional
from stock_market_psychology import analyze_market_psychology
from stock_news_engine import analyze_news
from stock_pattern_engine import analyze_patterns
from stock_risk_engine import calculate_risk_score
from stock_score_engine import calculate_scores
from stock_technical_engine import analyze_technical
from stock_trend_engine import build_trend_scenarios
from stock_utils import format_money, format_percent, format_price, safe_float
from stock_validation import StockInput, validate_user_inputs

st.set_page_config(page_title="Stock Decision Engine", layout="wide")


@st.cache_data(ttl=900, show_spinner=False)
def _cached_data(market: str, symbol: str, holding_days: int) -> dict[str, Any]:
    return load_stock_data(market, symbol, holding_days)


def _score(value: Any) -> str:
    return UNAVAILABLE if value == UNAVAILABLE else f"{safe_float(value):.0f}"


def _run(stock_input: StockInput) -> dict[str, Any]:
    data = _cached_data(stock_input.market, stock_input.symbol, stock_input.holding_days)
    technical = analyze_technical(data["history"])
    patterns = analyze_patterns(data["history"], technical)
    fundamental = analyze_fundamentals(data.get("fundamentals"))
    news = analyze_news(data.get("news"))
    institutional = analyze_institutional(stock_input.market, data.get("institutional"))
    psychology = analyze_market_psychology(data["history"], technical, patterns, news, institutional)
    risk = calculate_risk_score(data, technical, patterns, fundamental, news, institutional)
    scores = calculate_scores(technical, patterns, fundamental, news, institutional, psychology, risk)
    trend = build_trend_scenarios(technical, patterns, risk, scores, stock_input.holding_days)
    scores["trend_score"] = safe_float(trend.get("trend_score"), scores["trend_score"])
    price = safe_float(data.get("latest", {}).get("price"), technical.get("latest", {}).get("close", 0))
    capital = calculate_capital_plan(stock_input, price, technical, risk, trend, news)
    decision = make_final_decision(stock_input, technical, patterns, risk, trend, scores, news, institutional)
    return {"data": data, "technical": technical, "patterns": patterns, "fundamental": fundamental, "news": news, "institutional": institutional, "psychology": psychology, "risk": risk, "scores": scores, "trend": trend, "capital": capital, "decision": decision}


def _sidebar():
    st.sidebar.title("SDE 分析條件")
    market = st.sidebar.selectbox("市場選擇", [MARKET_TAIWAN, MARKET_US])
    symbol = st.sidebar.text_input("股票代號", value="2330" if market == MARKET_TAIWAN else "AAPL")
    capital = st.sidebar.number_input("投入資金", min_value=1000, value=DEFAULT_CAPITAL, step=10000)
    holding = st.sidebar.selectbox("持有期間", list(HOLDING_PERIODS.keys()), index=2)
    max_loss = st.sidebar.slider("最大可承受虧損比例", 1.0, 50.0, DEFAULT_MAX_LOSS_PERCENT, 0.5)
    style = st.sidebar.selectbox("交易風格", TRADING_STYLES, index=TRADING_STYLES.index(DEFAULT_TRADING_STYLE))
    staged = st.sidebar.checkbox("是否允許分批進場", value=True)
    trailing = st.sidebar.checkbox("是否使用移動停利", value=True)
    clicked = st.sidebar.button("Analyze", type="primary", use_container_width=True)
    validation = validate_user_inputs(market, symbol, capital, holding, max_loss, style, staged, trailing)
    for warning in validation.warnings:
        st.sidebar.warning(warning)
    return clicked, validation


def _metrics(decision: dict[str, Any]):
    cols = st.columns(6)
    cols[0].metric("Final Decision", decision["final_decision"])
    cols[1].metric("Trend Score", _score(decision["trend_score"]))
    cols[2].metric("Risk Score", _score(decision["risk_score"]))
    cols[3].metric("Entry Score", _score(decision["entry_score"]))
    cols[4].metric("Exit Score", _score(decision["exit_score"]))
    cols[5].metric("Confidence", _score(decision["confidence_score"]))


def _render(result: dict[str, Any]):
    data = result["data"]; latest = data["latest"]; company = data["company"]; tech = result["technical"]; indicators = tech.get("indicators")
    _metrics(result["decision"])
    st.subheader("1. 市場與股票輸入區 / 2. 即時價格區")
    if data.get("status") == UNAVAILABLE:
        st.warning("即時資料暫時無法取得；以下圖表使用安全示範序列維持分析流程。")
    cols = st.columns(5)
    cols[0].metric("股票名稱", company.get("name", data.get("symbol")))
    cols[1].metric("最新價格", format_price(latest.get("price")))
    cols[2].metric("日漲跌幅", format_percent(latest.get("daily_change_pct")))
    cols[3].metric("週漲跌幅", format_percent(latest.get("weekly_change_pct")))
    cols[4].metric("月漲跌幅", format_percent(latest.get("monthly_change_pct")))
    cols = st.columns(4)
    cols[0].metric("52 週高點", format_price(latest.get("week_52_high")))
    cols[1].metric("52 週低點", format_price(latest.get("week_52_low")))
    cols[2].metric("成交量", f"{int(safe_float(latest.get('volume'))):,}")
    cols[3].metric("資料來源", data.get("source", UNAVAILABLE))

    st.subheader("3. K 線圖"); st.plotly_chart(build_candlestick_chart(data["history"], indicators), use_container_width=True)
    st.subheader("4. 成交量圖"); st.plotly_chart(build_volume_chart(data["history"]), use_container_width=True)

    st.subheader("5. 技術指標區"); st.write(tech.get("explanation", ""))
    tl = tech.get("latest", {})
    st.dataframe(pd.DataFrame([
        {"Indicator": "MA20", "Value": format_price(tl.get("ma20"))}, {"Indicator": "MA60", "Value": format_price(tl.get("ma60"))}, {"Indicator": "MA120", "Value": format_price(tl.get("ma120"))}, {"Indicator": "RSI", "Value": f"{safe_float(tl.get('rsi'), 50):.2f}"}, {"Indicator": "ATR", "Value": format_price(tl.get("atr"))}, {"Indicator": "Volume Ratio", "Value": f"{safe_float(tl.get('volume_ratio'), 1):.2f}"}
    ]), use_container_width=True, hide_index=True)
    st.plotly_chart(build_technical_indicator_chart(indicators), use_container_width=True)

    st.subheader("6. 型態學分析區"); st.write(result["patterns"].get("summary", "")); st.dataframe(pd.DataFrame(result["patterns"].get("patterns", [])), use_container_width=True, hide_index=True)
    st.subheader("7. 財報分析區")
    f = result["fundamental"]; st.metric("Fundamental Score", _score(f.get("fundamental_score"))); st.write("支持因素：", f.get("support_factors", [])); st.write("風險因素：", f.get("risk_factors", []))
    if f.get("metrics"): st.dataframe(pd.DataFrame([{"Metric": k, "Value": v} for k, v in f["metrics"].items()]), use_container_width=True, hide_index=True)

    st.subheader("8. 新聞事件分析區")
    n = result["news"]; c = st.columns(4); c[0].metric("Sentiment", f"{safe_float(n.get('sentiment_score')):.2f}"); c[1].metric("Impact", n.get("impact_level")); c[2].metric("Risk", n.get("risk_level")); c[3].metric("Confidence", _score(n.get("confidence_score"))); st.write(n.get("summary", ""))
    if n.get("articles"): st.dataframe(pd.DataFrame(n["articles"]), use_container_width=True, hide_index=True)

    st.subheader("9. 法人 / 籌碼分析區")
    i = result["institutional"]; st.write(i.get("details", [])); st.metric("Institutional Score", _score(i.get("institutional_score")))
    st.subheader("10. 市場心理區")
    p = result["psychology"]; st.metric("Market Psychology Score", _score(p.get("market_psychology_score"))); st.write(p.get("market_psychology_label"), "-", p.get("reason"))

    st.subheader("11. 風險分析區")
    r = result["risk"]; cols = st.columns(4); cols[0].metric("Risk Score", _score(r.get("risk_score"))); cols[1].metric("Risk Level", r.get("risk_level")); cols[2].metric("ATR %", format_percent(r.get("atr_percent"))); cols[3].metric("Max Drawdown", format_percent(r.get("max_drawdown_percent")))
    st.plotly_chart(build_risk_radar_chart(r), use_container_width=True); st.dataframe(pd.DataFrame(r.get("top_risk_sources", [])), use_container_width=True, hide_index=True); st.info(r.get("risk_control_suggestion", ""))

    st.subheader("12. 趨勢情境預估區")
    t = result["trend"]; st.plotly_chart(build_scenario_chart(t), use_container_width=True)
    sc = t.get("scenarios", {}); cols = st.columns(3)
    for col, name in zip(cols, ["Bull Case", "Base Case", "Bear Case"]):
        s = sc.get(name, {}); col.metric(name, f"{safe_float(s.get('estimated_return_pct')):.2f}%", f"{safe_float(s.get('probability')):.0f}% 機率"); col.write("依據：", s.get("support_factors", [])); col.write("失效條件：", s.get("invalidation", ""))
    st.caption(f"三情境機率總和：{t.get('probability_sum', 0)}%")

    st.subheader("13. 資金管理區")
    cap = result["capital"]
    st.dataframe(pd.DataFrame([{"Item": k, "Value": v} for k, v in {
        "建議投入比例": format_percent(cap.get("suggested_allocation_pct")), "建議投入金額": format_money(cap.get("position_amount")), "第一次投入金額": format_money(cap.get("first_entry_amount")), "第二次投入金額": format_money(cap.get("second_entry_amount")), "第三次投入金額": format_money(cap.get("third_entry_amount")), "保留現金": format_money(cap.get("reserve_cash")), "停損價格": format_price(cap.get("stop_loss_price")), "停利價格": format_price(cap.get("take_profit_price")), "移動停利價格": format_price(cap.get("trailing_stop_price")), "預估最大虧損金額": format_money(cap.get("estimated_max_loss_amount")), "Bull Case 預估獲利": format_money(cap.get("bull_case_profit")), "Base Case 預估獲利": format_money(cap.get("base_case_profit")), "Bear Case 預估虧損": format_money(cap.get("bear_case_loss"))}.items()]), use_container_width=True, hide_index=True)

    st.subheader("14. 最終決策摘要區")
    d = result["decision"]; st.success(f"Final Decision：{d['final_decision']}")
    gc = st.columns(3); gc[0].plotly_chart(build_score_gauge("Trend Score", d["trend_score"], "#16a34a"), use_container_width=True); gc[1].plotly_chart(build_score_gauge("Risk Score", d["risk_score"], "#dc2626"), use_container_width=True); gc[2].plotly_chart(build_score_gauge("Confidence", d["confidence_score"], "#2563eb"), use_container_width=True)
    st.write("主要依據：", d.get("main_reasons", [])); st.write("風險說明：", d.get("risk_explanation", [])); st.write("適用條件：", d.get("applicable_conditions", [])); st.write("不適用情境：", d.get("not_applicable_scenarios", []))


def main():
    st.title(APP_NAME); st.caption(APP_TAGLINE); st.caption("本系統僅供研究與決策輔助，不構成任何投資建議；所有交易決策需由使用者自行承擔風險。")
    clicked, validation = _sidebar()
    if clicked:
        if not validation.ok:
            for error in validation.errors: st.error(error)
            return
        with st.spinner("正在讀取資料並建立多因子分析..."):
            st.session_state["sde_result"] = _run(validation.input_data)
    if "sde_result" not in st.session_state:
        st.info("請在左側輸入市場、股票代號與風險條件，按下 Analyze 後取得完整 Dashboard。")
        return
    for msg in st.session_state["sde_result"]["data"].get("errors", []): st.warning(msg)
    _render(st.session_state["sde_result"])


if __name__ == "__main__":
    main()
