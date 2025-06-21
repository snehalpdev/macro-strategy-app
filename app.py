import streamlit as st
import pandas as pd
import os
import json
import base64
from datetime import datetime
import pytz
from model import generate_trade_signal, load_model
from data import get_macro_data, get_price_data
from utils import load_secrets
from train_pipeline import run_training_pipeline
from report_generator import generate_pdf_report, streamlit_download_button
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from components.dashboard_insights import (
    log_signal_to_jsonl,
    display_signal_context,
    plot_price_with_regime,
    simulate_strategy_vs_hold
)


def is_market_open():
    now_utc = datetime.utcnow()
    est = pytz.utc.localize(now_utc).astimezone(pytz.timezone("US/Eastern"))
    open_time = est.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = est.replace(hour=16, minute=0, microsecond=0)
    return est.weekday() < 5 and open_time <= est <= close_time


st.set_page_config(page_title="Macro Strategy Dashboard", layout="wide", page_icon="📈")
secrets = load_secrets()
fred_key = secrets.get("FRED_API_KEY")
drive_id = secrets.get("GDRIVE_FOLDER_ID")


def download_latest_model_for_ticker(ticker, folder_id):
    encoded = os.getenv("GDRIVE_CREDENTIALS_JSON")
    creds = json.loads(base64.b64decode(encoded).decode())
    credentials = service_account.Credentials.from_service_account_info(creds)
    service = build("drive", "v3", credentials=credentials)
    prefix = f"model_{ticker.upper()}_"
    query = f"'{folder_id}' in parents and trashed = false and name contains '{prefix}'"
    files = service.files().list(q=query, fields="files(id, name, createdTime)").execute().get("files", [])
    if not files:
        raise FileNotFoundError(f"No model found for {ticker.upper()} in Drive")
    latest = max(files, key=lambda f: f["createdTime"])
    request = service.files().get_media(fileId=latest["id"])
    with open("model.json", "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    return latest["name"]


with st.sidebar:
    st.header("⚙️ Controls")
    ticker = st.text_input("Symbol", "SPY")
    lookback = st.slider("Lookback (days)", 30, 180, 90)
    st.markdown("---")
    status_text = "🟢 **OPEN**" if is_market_open() else "🔴 **CLOSED**"
    st.markdown(f"### 📈 Market Status: {status_text}")
    with st.expander("🛠️ Admin Panel"):
        if st.checkbox("I understand this will overwrite the model"):
            if st.button("🔁 Retrain Now"):
                with st.spinner("Retraining and uploading model..."):
                    result = run_training_pipeline(ticker=ticker)
                st.success(result)


try:
    model_file = download_latest_model_for_ticker(ticker, folder_id=drive_id)
    st.success(f"📥 Model loaded: {model_file}")
    model = load_model("model.json")
except Exception as e:
    st.error(f"❌ Could not load model: {e}")
    st.stop()


macro_df = get_macro_data(fred_key)
price_df = get_price_data(ticker, lookback)
if price_df.empty or macro_df.empty:
    st.error("⚠️ Data load failure. Check symbol or API keys.")
    st.stop()

latest_close_date = price_df.index[-1].strftime("%Y-%m-%d")
latest_close_price = float(price_df["Close"].iloc[-1])
st.info(f"📌 Latest available close price for **{ticker.upper()}** as of **{latest_close_date}**: **${latest_close_price:.2f}**")


try:
    regime, signal, confidence = generate_trade_signal(price_df, macro_df)
    latest_price = float(price_df["Close"].iloc[-1])
    timestamp = datetime.now().isoformat()
    new_signal = {
        "timestamp": timestamp,
        "ticker": ticker.upper(),
        "regime": regime,
        "signal": signal,
        "confidence": float(confidence),
        "price": latest_price
    }
    signal_entry = log_signal_to_jsonl(new_signal)
    display_signal_context(signal_entry, model_file)
except Exception as e:
    st.error(f"Prediction error: {e}")
    st.stop()


tab1, tab2 = st.tabs(["📊 Dashboard", "📜 Signal History"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### 📉 Price Chart with Regime Highlights")
        plot_price_with_regime()
    with col2:
        st.markdown("#### 🧠 Latest Macro Snapshot")
        st.dataframe(macro_df.tail(5), use_container_width=True)

    st.markdown("---")
    simulate_strategy_vs_hold()

    with st.expander("ℹ️ What does this chart mean?"):
        st.markdown("""
### 📊 Strategy vs Buy & Hold Explained

This chart simulates two paths your capital could take:

- **📈 Strategy Line**: Invest only when the model says **Buy**.
- **📊 Buy & Hold Line**: Always stay in the market.

📌 No trading fees or slippage are applied — just pure signal-based simulation.
""")


with tab2:
    st.subheader("📜 Signal Log")
    try:
        with open("logs/signal_log.jsonl") as f:
            rows = [json.loads(line) for line in f]
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df[df["ticker"].str.upper() == ticker.upper()]

        df["returns"] = 0.0
        for i in range(len(df) - 1):
            if df.loc[i, "signal"] == "Buy":
                df.loc[i + 1, "returns"] = (df.loc[i + 1, "price"] / df.loc[i, "price"]) - 1
        df["strategy_equity"] = (1 + df["returns"]).cumprod()
        df["buy_hold"] = df["price"] / df["price"].iloc[0]

        st.markdown("#### 📈 Strategy vs Buy & Hold")
        st.line_chart(df.set_index("timestamp")[["strategy_equity", "buy_hold"]])

        st.markdown("#### 📌 Performance Metrics")
        returns = df["strategy_equity"].pct_change().dropna()
        volatility = returns.std()
        sharpe = returns.mean() / volatility * (252 ** 0.5) if volatility > 0 else float("nan")
        metrics = {
            "Total Return (Strategy)": f"{df['strategy_equity'].iloc[-1] - 1:.2%}",
            "Total Return (Buy & Hold)": f"{df['buy_hold'].iloc[-1] - 1:.2%}",
            "Annualized Return": f"{(df['strategy_equity'].iloc[-1]) ** (252 / len(df)) - 1:.2%}",
            "Volatility": f"{volatility * (252 ** 0.5):.2%}",
            "Sharpe Ratio": f"{sharpe:.2f}",
            "Max Drawdown": f"{((df['strategy_equity'].cummax() - df['strategy_equity']) / df['strategy_equity'].cummax()).max():.2%}"
        }
        for key, val in metrics.items():
            st.write(f"- **{key}**: {val}")

        if st.button("📄 Export Strategy Report"):
            recent = df[["timestamp", "ticker", "regime", "signal", "confidence"]].tail(10)
            pdf_path = generate_pdf_report(metrics, df.iloc[-1], recent, df)
            st.markdown(streamlit_download_button(pdf_path), unsafe_allow_html=True)

        st.markdown("#### 🧾 Full Signal Log")
        st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)

    except FileNotFoundError:
        st.info("No signal logs yet.")