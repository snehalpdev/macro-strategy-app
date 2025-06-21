import streamlit as st
import pandas as pd
import os
import json
import base64
from datetime import datetime, timedelta
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

st.set_page_config(page_title="Macro Strategy Dashboard", layout="wide", page_icon="📈")
secrets = load_secrets()
fred_key = secrets.get("FRED_API_KEY")
drive_id = secrets.get("GDRIVE_FOLDER_ID")

def is_market_open():
    now_utc = datetime.utcnow()
    est = pytz.utc.localize(now_utc).astimezone(pytz.timezone("US/Eastern"))
    open_time = est.replace(hour=9, minute=30)
    close_time = est.replace(hour=16, minute=0)
    return est.weekday() < 5 and open_time <= est <= close_time

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
            _, done = downloader.next_chunk()
    return latest["name"]
    # --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Symbol & Model Controls")

    # Load available model list (assumes saved locally or use your GDrive filenames)
    model_files = [f for f in os.listdir("models") if f.startswith("model_") and f.endswith(".json")]
    available_tickers = sorted(list({f.split("_")[1] for f in model_files}))

    selected_ticker = st.selectbox("📂 Load Existing Model", available_tickers) if available_tickers else ""
    st.caption(f"✅ Using model for `{selected_ticker}`")

    st.markdown("---")

    st.markdown("### ➕ Retrain New Symbol")
    new_ticker = st.text_input("🔤 Type a new ticker symbol", "").strip().upper()

    if new_ticker:
        st.warning(f"🚧 No model found for `{new_ticker}`. You need to retrain it before use.")
        if st.button("📚 Retrain Now"):
            with st.spinner("Training and uploading..."):
                result = run_training_pipeline(ticker=new_ticker)
            st.success(result)
            st.experimental_rerun()

    # Final symbol to use
    ticker = new_ticker if new_ticker else selected_ticker

    lookback = st.slider("📅 Lookback Window", 30, 180, 90)

    st.markdown("---")

    market_open = is_market_open()
    st.markdown(f"📈 Market Status: {'🟢 OPEN' if market_open else '🔴 CLOSED'}")

    # Refresh controls
    now = datetime.utcnow()
    if "last_fetch" not in st.session_state:
        st.session_state.last_fetch = None
    if "cached_price_df" not in st.session_state:
        st.session_state.cached_price_df = None

    refresh_now = st.button("🔄 Refresh Now")
    time_elapsed = (now - st.session_state.last_fetch) if st.session_state.last_fetch else timedelta(minutes=999)
    data_stale = time_elapsed > timedelta(minutes=5)
    needs_refresh = refresh_now or (market_open and data_stale) or (st.session_state.cached_price_df is None)

    if not market_open:
        st.caption("🔒 Market is closed. No live updates.")
    elif data_stale:
        st.warning("⚠️ Data may be stale. Auto-refresh runs every 5 minutes.")
    else:
        st.caption(f"⏱️ Last fetched: {time_elapsed.total_seconds() / 60:.1f} min ago.")
        # --- Load model for selected symbol ---
try:
    model_file = download_latest_model_for_ticker(ticker, folder_id=drive_id)
    st.success(f"📥 Model loaded: {model_file}")
    model = load_model("model.json")
except Exception as e:
    st.error(f"❌ Could not load model: {e}")
    st.stop()

# --- Fetch data ---
macro_df = get_macro_data(fred_key)
if needs_refresh:
    st.session_state.cached_price_df = get_price_data(ticker, lookback)
    st.session_state.last_fetch = now

price_df = st.session_state.cached_price_df
if price_df is None or price_df.empty or macro_df.empty:
    st.error("⚠️ Data load failure. Check symbol or API keys.")
    st.stop()

# --- Show latest close price
latest_close_date = price_df.index[-1].strftime("%Y-%m-%d")
latest_close_price = float(price_df["Close"].iloc[-1])
st.info(f"📌 Latest available close price for **{ticker}** as of **{latest_close_date}**: **${latest_close_price:.2f}**")

# --- Generate signal
try:
    regime, signal, confidence = generate_trade_signal(price_df, macro_df)
    signal_data = {
        "timestamp": datetime.now().isoformat(),
        "ticker": ticker,
        "regime": regime,
        "signal": signal,
        "confidence": float(confidence),
        "price": latest_close_price
    }
    entry = log_signal_to_jsonl(signal_data)
    display_signal_context(entry, model_file)
except Exception as e:
    st.error(f"Prediction error: {e}")
    st.stop()

# --- Dashboard Tabs ---
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

with tab2:
    st.subheader("📜 Signal Log & Backtest Metrics")
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

        returns = df["strategy_equity"].pct_change().dropna()
        volatility = returns.std()
        sharpe = returns.mean() / volatility * (252**0.5) if volatility > 0 else float("nan")
        drawdown = ((df["strategy_equity"].cummax() - df["strategy_equity"]) / df["strategy_equity"].cummax()).max()

        metrics = {
            "Total Return (Strategy)": f"{df['strategy_equity'].iloc[-1] - 1:.2%}",
            "Total Return (Buy & Hold)": f"{df['buy_hold'].iloc[-1] - 1:.2%}",
            "Annualized Return": f"{(df['strategy_equity'].iloc[-1]) ** (252 / len(df)) - 1:.2%}",
            "Volatility": f"{volatility * (252 ** 0.5):.2%}",
            "Sharpe Ratio": f"{sharpe:.2f}",
            "Max Drawdown": f"{drawdown:.2%}"
        }

        st.markdown("#### 📌 Performance Metrics")
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