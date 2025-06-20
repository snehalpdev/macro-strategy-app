import pandas as pd
import yfinance as yf
import requests

def get_price_data(ticker, days):
    try:
        df = yf.download(ticker, period=f"{days}d", progress=False)
        return df
    except:
        return pd.DataFrame()

def get_macro_data(fred_key):
    # Mocked sample macro data for now
    data = {
        "inflation": [0.025, 0.03, 0.032],
        "interest_rate": [0.015, 0.02, 0.025],
        "gdp": [2.5, 1.8, -0.5]
    }
    df = pd.DataFrame(data)
    return df