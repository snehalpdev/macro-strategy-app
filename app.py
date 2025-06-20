import streamlit as st
import pandas as pd
from model import generate_trade_signal
from data import get_macro_data, get_price_data
from utils import load_secrets

st.set_page_config(page_title="Macro Strategy Dashboard", layout="wide")
st.title("📈 Macro-Aware Trading Strategy")

ticker = st.sidebar.text_input("Enter Ticker Symbol", "SPY")
lookback = st.sidebar.slider("Price Lookback (days)", 30, 180, 90)

# Load API secrets
secrets = load_secrets()
fred_key = secrets.get("FRED_API_KEY")
macro_df = get_macro_data(fred_key)

# Load asset price history
price_df = get_price_data(ticker, lookback)

if not price_df.empty:
    st.subheader(f"{ticker} - Price & Macro Overview")
    st.line_chart(price_df['Close'])
    st.dataframe(macro_df.tail(5))

    regime, signal, confidence = generate_trade_signal(price_df, macro_df)
    st.subheader("🔍 Signal Insight")
    st.markdown(f"- **Detected Regime:** {regime}")
    st.markdown(f"- **Trade Signal:** {signal}")
    st.markdown(f"- **Model Confidence:** {confidence:.2f}%")

else:
    st.warning("Unable to load data. Please check ticker symbol or try again.")