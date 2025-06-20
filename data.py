import pandas as pd
import yfinance as yf
from fredapi import Fred

def get_price_data(ticker="SPY", lookback=90):
    try:
        df = yf.download(ticker, period=f"{lookback}d", progress=False)
        df = df[["Close"]]
        return df.dropna()
    except Exception as e:
        print(f"Failed to load price data: {e}")
        return pd.DataFrame()

def get_macro_data(fred_key):
    try:
        fred = Fred(api_key=fred_key)
        indicators = {
            "UNRATE": "Unemployment Rate",
            "CPIAUCSL": "Consumer Price Index",
            "FEDFUNDS": "Fed Funds Rate",
            "INDPRO": "Industrial Production",
            "GS10": "10-Year Treasury Yield"
        }

        df = pd.DataFrame()
        for code, name in indicators.items():
            series = fred.get_series(code)
            df[name] = series
        df = df.fillna(method="ffill").dropna()
        return df.tail(100).reset_index(drop=True)
    except Exception as e:
        print(f"Failed to load macro data: {e}")
        return pd.DataFrame()