# Stock Decision Engine（SDE）

Stock Decision Engine（SDE）是一套可部署到 Streamlit Community Cloud 的股票交易決策輔助 Web App，同時支援台股與美股。系統以多因子資料建立 Dashboard，協助使用者檢視進場、退場、觀望、等待突破、等待回檔、分批布局、續抱、減碼、停利、停損與資金配置風險。

SDE 不是股價預言工具，也不是自動下單工具。所有輸出都以數據、分數、機率、情境分析、風險評估與明確理由呈現。

## 支援市場

- 台股：支援 `2330`、`2330.TW`、`8069.TWO`。若市場選擇台股且輸入純數字，系統會自動轉為 Yahoo Finance 格式。
- 美股：支援 `AAPL`、`MSFT`、`NVDA`、`TSLA`、`AMD`、`META`、`GOOGL` 等代號。
- ETF、台股法人資料、美股機構資料、選股器、回測與交易日誌已預留擴充介面。

## 功能

- 即時價格與 OHLC 資料讀取
- K 線圖、成交量圖、技術指標圖
- MA、EMA、MACD、RSI、KD、ATR、Bollinger Bands、VWAP、OBV、ADX、Volume Ratio
- 型態學分析：突破壓力、跌破支撐、平台整理、假突破、多頭排列、空頭排列、雙底、雙頭、三角收斂、旗形
- 財報分析模組，資料缺失時顯示 `unavailable`
- 新聞事件 mock interface，方便未來串接真實新聞 API
- 法人 / 籌碼分析模組，資料缺失時顯示 `unavailable`
- Risk Score、Trend Score、Entry Score、Exit Score、Confidence Score
- Bull / Base / Bear 三情境趨勢預估，機率總和為 100%
- 資金管理模擬：投入比例、分批金額、保留現金、停損、停利、移動停利、情境損益
- Rule-based final decision engine，所有建議都附上理由與不適用情境

## 股票專屬檔案架構

```text
stock_app.py
stock_data_loader.py
stock_technical_engine.py
stock_pattern_engine.py
stock_fundamental_engine.py
stock_news_engine.py
stock_institutional_engine.py
stock_market_psychology.py
stock_risk_engine.py
stock_trend_engine.py
stock_decision_engine.py
stock_capital_manager.py
stock_config.py
stock_utils.py
stock_constants.py
stock_chart_builder.py
stock_score_engine.py
stock_validation.py
requirements.txt
README.md
```

## Streamlit Community Cloud 部署

1. 將本專案推送到 GitHub repository。
2. 到 Streamlit Community Cloud 建立新 App。
3. Repository 選擇此專案。
4. Branch 選擇部署分支。
5. Main file path 指定為：

```text
stock_app.py
```

6. 部署後開啟網址，左側輸入市場、股票代號、投入資金、持有期間、最大可承受虧損比例與交易風格，按下 Analyze。

## API Key 設定

目前 MVP 主要使用 `yfinance`。若未來串接 Alpha Vantage、Financial Modeling Prep、FinMind 或 Fugle，請使用 Streamlit Secrets 或環境變數設定，例如：

```toml
ALPHA_VANTAGE_API_KEY = "your_key"
FMP_API_KEY = "your_key"
FINMIND_API_KEY = "your_key"
FUGLE_API_KEY = "your_key"
```

程式會先讀取 Streamlit Secrets，再讀取環境變數。API Key 不需寫入程式碼。

## 已知限制

- yfinance、新聞、法人籌碼與財報資料可能因資料來源限制而暫時不可用。
- 台股上櫃股票若輸入純數字，系統預設轉為 `.TW`；上櫃股票請直接輸入 `.TWO`。
- 財報、新聞與法人籌碼資料不足時，系統會顯示 `unavailable`，並以中性分數維持 Dashboard 運作。
- 情境預估是基於規則與歷史波動資料的決策輔助，不是確定性價格預測。

## 未來擴充方向

- 串接台股三大法人、融資、融券與借券資料
- 串接美股機構持股、內部人交易、空單與 options flow
- 串接真實新聞情緒 API
- 建立 ETF 第二版支援
- 建立 Screener 選股器
- 建立回測模組
- 建立 Trading Journal 投資日誌
- 加入更完整的產業與大盤風險模型

## 免責聲明

本系統僅供研究與決策輔助，不構成任何投資建議。本系統不保證獲利，也無法避免虧損。所有交易決策需由使用者自行承擔風險。
