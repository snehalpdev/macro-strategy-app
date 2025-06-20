import streamlit as st
import pandas as pd
from model import generate_trade_signal, load_model, build_features
from data import get_macro_data, get_price_data
from utils import load_secrets
from train_pipeline import run_training_pipeline
from alerts import send_email_alert
from report_generator import generate_pdf_report, streamlit_download_button
from datetime import datetime
import json
import os

# ----- Setup -----
st.set_page_config(page_title="Macro Strategy Dashboard", layout="wide", page_icon="📈")
secrets = load_secrets()
fred_key = secrets.get("FRED_API_KEY")
import streamlit as st
st.write("🔑 FRED key loaded:", "FRED_API_KEY" in st.secrets)
st.write("🔍 st.secrets keys:", list(st.secrets.keys()))

# ----- Controls -----
with st.sidebar:
    st.header("⚙️ Controls")
    ticker = st.text_input("Symbol", "SPY")
    lookback = st.slider("Lookback (days)", 30, 180, 90)

    st.markdown("---")
    with st.expander("🛠️ Admin Panel"):
        confirm = st.checkbox("I understand this will overwrite the model")
        if confirm:
            if st.button("🔁 Retrain Now"):
                with st.spinner("Retraining and uploading model..."):
                    result = run_training_pipeline()
                st.success(result)

# ----- Load Data -----
macro_df = get_macro_data(fred_key)
price_df = get_price_data(ticker, lookback)
st.write("📊 Price data loaded:", not price_df.empty)
st.write("🏦 Macro data loaded:", not macro_df.empty)

if price_df.empty or macro_df.empty:
    st.warning("⚠️ Unable to load data. Check ticker or API keys.")
    st.stop()

# ----- Signal Prediction -----
try:
    regime, signal, confidence = generate_trade_signal(price_df, macro_df)
    latest_price = price_df["Close"].iloc[-1]
    timestamp = datetime.now().isoformat()

    st.subheader("📈 Current Signal")
    st.info(f"**Regime:** {regime} | **Signal:** {signal} | **Confidence:** {confidence:.2f}%")

    # Log signal
    os.makedirs("logs", exist_ok=True)
    with open("logs/signal_log.jsonl", "a") as f:
        f.write(json.dumps({
            "timestamp": timestamp,
            "ticker": ticker,
            "regime": regime,
            "signal": signal,
            "confidence": confidence,
            "price": latest_price
        }) + "\n")

    # Optional alert
    if confidence > 85:
        send_email_alert(signal, confidence, "your@email.com")

except Exception as e:
    st.error(f"Prediction failed: {e}")
    st.stop()

# ----- Signal History Tab -----
tab1, tab2 = st.tabs(["📊 Dashboard", "📜 Signal History"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Price History**")
        st.line_chart(price_df['Close'])
    with col2:
        st.markdown("**Latest Macro Data**")
        st.dataframe(macro_df.tail(5), use_container_width=True)

with tab2:
    st.subheader("📜 Signal Log")
    try:
        with open("logs/signal_log.jsonl") as f:
            data = [json.loads(line) for line in f]
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            df["returns"] = 0.0
            for i in range(len(df) - 1):
                if df.loc[i, "signal"] == "Buy":
                    delta = (df.loc[i + 1, "price"] / df.loc[i, "price"]) - 1
                    df.loc[i + 1, "returns"] = delta
            df["strategy_equity"] = (1 + df["returns"]).cumprod()
            df["buy_hold"] = df["price"] / df["price"].iloc[0]

            st.markdown("#### 📈 Strategy vs Benchmark")
            st.line_chart(df.set_index("timestamp")[["strategy_equity", "buy_hold"]])

            st.markdown("#### 📌 Performance Metrics")
            returns = df["strategy_equity"].pct_change().dropna()
            metrics = {
                "Total Return (Strategy)": f"{df['strategy_equity'].iloc[-1] - 1:.2%}",
                "Total Return (Buy & Hold)": f"{df['buy_hold'].iloc[-1] - 1:.2%}",
                "Annualized Return": f"{(df['strategy_equity'].iloc[-1]) ** (252 / len(df)) - 1:.2%}",
                "Volatility": f"{returns.std() * (252 ** 0.5):.2%}",
                "Sharpe Ratio": f"{returns.mean() / returns.std() * (252 ** 0.5):.2f}",
                "Max Drawdown": f"{((df['strategy_equity'].cummax() - df['strategy_equity']) / df['strategy_equity'].cummax()).max():.2%}",
            }
            for k, v in metrics.items():
                st.write(f"- **{k}**: {v}")

            if st.button("📄 Export Strategy Report"):
                latest = df.iloc[-1]
                recent = df[["timestamp", "ticker", "regime", "signal", "confidence"]].tail(10)
                pdf_path = generate_pdf_report(metrics, latest, recent, df)
                st.markdown(streamlit_download_button(pdf_path), unsafe_allow_html=True)

            st.markdown("#### 🧾 Full Log")
            st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)

    except FileNotFoundError:
        st.info("No logged signals yet.")