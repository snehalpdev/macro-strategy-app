import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
import yfinance as yf

def _prep_price_df(price_df):
    price_df = price_df.reset_index()
    if isinstance(price_df.columns, pd.MultiIndex):
        price_df.columns = price_df.columns.get_level_values(-1)

    time_col = next((col for col in ["Date", "date", "Datetime", "index", price_df.columns[0]] if col in price_df.columns), None)
    price_df["timestamp"] = pd.to_datetime(price_df[time_col], errors="coerce")

    # 🔄 Fallback if 'Close' is missing
    if "Close" not in price_df.columns and "Adj Close" in price_df.columns:
        st.warning("⚠️ 'Close' column missing — using 'Adj Close' instead.")
        price_df["Close"] = price_df["Adj Close"]

    if "Close" not in price_df.columns:
        st.warning("📉 Could not find usable 'Close' price data — skipping chart.")
        return pd.DataFrame()

    price_df = price_df[["timestamp", "Close"]].dropna()
    return price_df


def plot_price_with_regime(log_path="logs/signal_log.jsonl"):
    try:
        with open(log_path) as f:
            entries = [json.loads(line) for line in f if line.strip()]
        df = pd.DataFrame(entries)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        ticker = df["ticker"].iloc[-1]
        start = df["timestamp"].min().strftime("%Y-%m-%d")

        price_df = yf.download(ticker, start=start, auto_adjust=True)
        price_df = _prep_price_df(price_df)
        if price_df.empty:
            st.info("📭 No price data available to generate the price chart.")
            return

        merged = pd.merge_asof(price_df, df[["timestamp", "regime", "signal"]], on="timestamp", direction="backward")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=merged["timestamp"], y=merged["Close"],
                                 mode="lines", name="Price", line=dict(color="black")))

        colors = {"Bullish": "rgba(76,175,80,0.2)", "Bearish": "rgba(244,67,54,0.2)", "Neutral": "rgba(255,193,7,0.2)"}
        last_regime = None
        start_time = None
        for i in range(len(merged)):
            curr = merged.iloc[i]
            if curr["regime"] != last_regime:
                if last_regime and start_time:
                    fig.add_vrect(x0=start_time, x1=curr["timestamp"],
                                  fillcolor=colors.get(last_regime, "gray"), opacity=0.2, line_width=0)
                start_time = curr["timestamp"]
                last_regime = curr["regime"]
        if start_time and last_regime:
            fig.add_vrect(x0=start_time, x1=merged["timestamp"].iloc[-1],
                          fillcolor=colors.get(last_regime, "gray"), opacity=0.2, line_width=0)

        buys = merged[merged["signal"] == "Buy"]
        sells = merged[merged["signal"] == "Sell"]
        fig.add_trace(go.Scatter(x=buys["timestamp"], y=buys["Close"],
                                 mode="markers", name="Buy Signal",
                                 marker=dict(symbol="triangle-up", color="green", size=10)))
        fig.add_trace(go.Scatter(x=sells["timestamp"], y=sells["Close"],
                                 mode="markers", name="Sell Signal",
                                 marker=dict(symbol="triangle-down", color="red", size=10)))

        fig.update_layout(title="📊 Price with Regimes & Signals",
                          xaxis_title="Date", yaxis_title="Price", height=400)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning(f"Could not render chart: {e}")


def simulate_strategy_vs_hold(log_path="logs/signal_log.jsonl"):
    try:
        with open(log_path) as f:
            logs = [json.loads(line) for line in f if line.strip()]
        df = pd.DataFrame(logs)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        ticker = df["ticker"].iloc[-1]
        start = df["timestamp"].min().strftime("%Y-%m-%d")

        price_df = yf.download(ticker, start=start, auto_adjust=True)
        price_df = _prep_price_df(price_df)
        if price_df.empty:
            st.info("📭 No price data available to simulate performance.")
            return

        merged = pd.merge_asof(price_df, df[["timestamp", "signal"]], on="timestamp", direction="backward")
        merged["signal"] = merged["signal"].ffill()
        merged["daily_return"] = merged["Close"].pct_change()
        merged["strategy_return"] = np.where(merged["signal"] == "Buy", merged["daily_return"], 0)
        merged["equity_curve"] = (1 + merged["strategy_return"]).cumprod()
        merged["buy_hold_curve"] = (1 + merged["daily_return"]).cumprod()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=merged["timestamp"], y=merged["equity_curve"],
                                 mode="lines", name="📈 Strategy"))
        fig.add_trace(go.Scatter(x=merged["timestamp"], y=merged["buy_hold_curve"],
                                 mode="lines", name="📊 Buy & Hold", line=dict(dash="dot")))

        fig.update_layout(title="📈 Strategy vs Buy & Hold Performance",
                          xaxis_title="Date", yaxis_title="Cumulative Return", height=400)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning(f"Could not simulate performance: {e}")