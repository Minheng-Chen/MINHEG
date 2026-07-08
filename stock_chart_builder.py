from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from stock_utils import safe_float


def _empty(title: str) -> go.Figure:
    fig = go.Figure(); fig.update_layout(title=title, height=330, template="plotly_white"); fig.add_annotation(text="資料不足或暫時無法取得", x=.5, y=.5, showarrow=False, xref="paper", yref="paper"); return fig


def build_candlestick_chart(history: pd.DataFrame, indicators: pd.DataFrame | None = None) -> go.Figure:
    if history is None or history.empty: return _empty("K 線圖")
    fig = go.Figure(go.Candlestick(x=history.index, open=history["Open"], high=history["High"], low=history["Low"], close=history["Close"], name="K 線"))
    if indicators is not None and not indicators.empty:
        for col, color in [("MA20", "#2563eb"), ("MA60", "#f97316"), ("MA120", "#64748b")]:
            if col in indicators: fig.add_trace(go.Scatter(x=indicators.index, y=indicators[col], name=col, mode="lines", line=dict(color=color, width=1.4)))
    fig.update_layout(title="K 線與主要均線", height=520, template="plotly_white", xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=60, b=20)); return fig


def build_volume_chart(history: pd.DataFrame) -> go.Figure:
    if history is None or history.empty: return _empty("成交量")
    colors = ["#16a34a" if c >= o else "#dc2626" for c, o in zip(history["Close"], history["Open"])]
    fig = go.Figure(go.Bar(x=history.index, y=history["Volume"], marker_color=colors)); fig.update_layout(title="成交量", height=300, template="plotly_white"); return fig


def build_technical_indicator_chart(indicators: pd.DataFrame) -> go.Figure:
    if indicators is None or indicators.empty: return _empty("技術指標")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("RSI / KD", "MACD"))
    for col, color in [("RSI", "#7c3aed"), ("K", "#0891b2"), ("D", "#ea580c")]:
        if col in indicators: fig.add_trace(go.Scatter(x=indicators.index, y=indicators[col], name=col, line=dict(color=color)), row=1, col=1)
    if "MACD" in indicators: fig.add_trace(go.Scatter(x=indicators.index, y=indicators["MACD"], name="MACD"), row=2, col=1)
    if "MACD_SIGNAL" in indicators: fig.add_trace(go.Scatter(x=indicators.index, y=indicators["MACD_SIGNAL"], name="Signal"), row=2, col=1)
    if "MACD_HIST" in indicators: fig.add_trace(go.Bar(x=indicators.index, y=indicators["MACD_HIST"], name="Histogram"), row=2, col=1)
    fig.update_layout(height=520, template="plotly_white", legend=dict(orientation="h")); return fig


def build_risk_radar_chart(risk: dict[str, Any]) -> go.Figure:
    comp = risk.get("components", {})
    if not comp: return _empty("風險雷達圖")
    labels = list(comp.keys()); values = [safe_float(comp[k].get("score")) for k in labels]
    fig = go.Figure(go.Scatterpolar(r=values + values[:1], theta=labels + labels[:1], fill="toself", line=dict(color="#dc2626")))
    fig.update_layout(title="風險雷達圖", polar=dict(radialaxis=dict(range=[0, 100])), showlegend=False, height=430, template="plotly_white"); return fig


def build_scenario_chart(trend: dict[str, Any]) -> go.Figure:
    scenarios = trend.get("scenarios", {})
    if not scenarios: return _empty("情境報酬圖")
    names = list(scenarios.keys()); returns = [safe_float(scenarios[n].get("estimated_return_pct")) for n in names]; probs = [safe_float(scenarios[n].get("probability")) for n in names]
    fig = go.Figure(go.Bar(x=names, y=returns, marker_color=["#16a34a" if v >= 0 else "#dc2626" for v in returns], text=[f"{p:.0f}% 機率" for p in probs], textposition="outside"))
    fig.update_layout(title="Bull / Base / Bear 情境報酬", yaxis_title="預估報酬率 (%)", height=360, template="plotly_white"); return fig


def build_score_gauge(title: str, value: float, color: str = "#2563eb") -> go.Figure:
    fig = go.Figure(go.Indicator(mode="gauge+number", value=safe_float(value), title={"text": title}, gauge={"axis": {"range": [0, 100]}, "bar": {"color": color}}))
    fig.update_layout(height=250, template="plotly_white", margin=dict(l=10, r=10, t=45, b=10)); return fig
