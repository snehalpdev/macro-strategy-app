import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
import yfinance as yf


# --- 1. Smart signal logging ---
def log_signal_to_jsonl(new_entry, log_path="logs/signal_log.jsonl"):
    os.makedirs("logs", exist_ok=True)
    new_entry = {k: float(v) if hasattr(v, "item") else v for k, v in new_entry.items()}

    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            lines = f.readlines()
            if lines:
                last_entry = json.loads(lines[-1])
                keys = ["ticker", "regime", "signal"]
                if all(new_entry.get(k) == last_entry.get(k) for k in keys):
                    return last_entry  # signal unchanged → do not log

    with open(log_path, "a") as f:
        f.write(json.dumps(new_entry) + "\n")
    return new_entry


# --- 2. Display signal context box ---
def display_signal_context(signal_entry, model_name):
    st.subheader("📈 Signal")
    is_fresh = signal_entry["timestamp"] == get_last_signal_timestamp()
    st.markdown(f"""
**Regime**: {signal_entry['regime']}  
**Signal**: {signal_entry['signal']}  
**Confidence**: {signal_entry['confidence']:.2f}%
""")
    st.markdown(f"""
🧠 Model: `{model_name}`  
📅 Generated on: `{signal_entry['timestamp']}`  
💰 Price at signal: `{signal_entry['price']:.2f}`
""")
    if is_fresh:
        st.success("✅ New signal generated and logged.")
    else:
        st.info("📌 Market unchanged — last signal is still valid.")

    elapsed = (datetime.now() - datetime.fromisoformat(signal_entry['timestamp'])).total_seconds() / 60
    st.caption(f"⏱️ Last update: **{elapsed:.1f} min ago**")


def get_last_signal_timestamp(log_path="logs/signal_log.jsonl"):
    try:
        with open(log_path) as f:
            lines = f.readlines()
            if lines:
                return json.loads(lines[-1])["timestamp"]
    except:
        return ""


# --- 3. Plot price with regime background + buy/sell markers ---
def plot_price_with_regime(log_path="logs/signal_log.jsonl"):
    try:
        with open(log_path) as f:
            entries = [json.loads(line) for line in f if line.strip()]
        df = pd.DataFrame(entries)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        ticker = df["ticker"].iloc[-1]

        # Fetch price
        start = df["timestamp"].min().strftime("%Y-%m-%d")
        price_df = yf.download(ticker, start=start)
        price_df.reset_index(inplace=True)
        price_df["timestamp"] = pd.to_datetime(price_df["Date"])

        merged = pd.merge_asof(price_df, df[["timestamp", "regime", "signal"]],
                               on="timestamp", direction="backward")

        colors = {"Bullish": "rgba(76,175,80,0.2)", "Bearish": "rgba(244,67,54,0.2)",
                  "Neutral": "rgba(255,193,7,0.2)"}

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=merged["timestamp"], y=merged["Close"],
                                 mode="lines", name="Price", line=dict(color="black")))

        # Regime shading
        start_time = None
        last_regime = None
        for i in range(len(merged)):
            current = merged.loc[i]
            if current["regime"] != last_regime:
                if start_time and last_regime:
                    fig.add_vrect(x0=start_time, x1=current["timestamp"],
                                  fillcolor=colors.get(last_regime, "gray"), opacity=0.2, line_width=0)
                start_time = current["timestamp"]
                last_regime = current["regime"]
        if start_time and last_regime:
            fig.add_vrect(x0=start_time, x1=merged["timestamp"].iloc[-1],
                          fillcolor=colors.get(last_regime, "gray"), opacity=0.2, line_width=0)

        # Buy/Sell markers
        buys = merged[merged["signal"] == "Buy"]
        sells = merged[merged["signal"] == "Sell"]
        fig.add_trace(go.Scatter(x=buys["timestamp"], y=buys["Close"], mode="markers",
                                 marker=dict(color="green", symbol="triangle-up", size=10),
                                 name="Buy Signal"))
        fig.add_trace(go.Scatter(x=sells["timestamp"], y=sells["Close"], mode="markers",
                                 marker=dict(color="red", symbol="triangle-down", size=10),
                                 name="Sell Signal"))

        fig.update_layout(title="📊 Price with Regime & Signals",
                          xaxis_title="Date", yaxis_title="Price", height=400)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning(f"Could not render chart: {e}")


# --- 4. Simulate performance ---
def simulate_strategy_vs_hold(log_path="logs/signal_log.jsonl"):
    try:
        with open(log_path) as f:
            logs = [json.loads(line) for line in f if line.strip()]
        df = pd.DataFrame(logs)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        ticker = df["ticker"].iloc[-1]

        start = df["timestamp"].min().strftime("%Y-%m-%d")
        price_df = yf.download(ticker, start=start)
        price_df.reset_index(inplace=True)
        price_df["timestamp"] = pd.to_datetime(price_df["Date"])

        merged = pd.merge_asof(price_df, df[["timestamp", "signal"]], on="timestamp", direction="backward")
        merged["signal"].fillna(method="ffill", inplace=True)
        merged["daily_return"] = merged["Close"].pct_change()
        merged["strategy_return"] = np.where(merged["signal"] == "Buy", merged["daily_return"], 0)
        merged["equity_curve"] = (1 + merged["strategy_return"]).cumprod()
        merged["buy_hold_curve"] = (1 + merged["daily_return"]).cumprod()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=merged["timestamp"], y=merged["equity_curve"],
                                 mode="lines", name="📈 Strategy"))
        fig.add_trace(go.Scatter(x=merged["timestamp"], y=merged["buy_hold_curve"],
                                 mode="lines", name="📊 Buy & Hold", line=dict(dash="dot")))

        fig.update_layout(title="📈 Strategy vs Buy & Hold",
                          yaxis_title="Cumulative Return", height=400)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning(f"Could not simulate performance: {e}")