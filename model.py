import xgboost as xgb
import pandas as pd
import numpy as np
import json

def load_model(model_path="model.json"):
    model = xgb.XGBClassifier()
    model.load_model(model_path)
    return model

def build_features(price_df, macro_df):
    df = price_df.copy()
    df["return"] = df["Close"].pct_change()
    df["volatility"] = df["Close"].rolling(window=10).std()
    df["momentum"] = df["Close"] - df["Close"].shift(10)
    df = df.dropna()

    latest_price_features = df[["return", "volatility", "momentum"]].iloc[-1:]

    latest_macro = macro_df.iloc[-1:].copy()
    macro_features = latest_macro.select_dtypes(include=[np.number])

    features = pd.concat([latest_price_features.reset_index(drop=True),
                          macro_features.reset_index(drop=True)], axis=1)
    return features

def generate_trade_signal(price_df, macro_df):
    model = load_model()
    X = build_features(price_df, macro_df)

    pred_prob = model.predict_proba(X)[0]
    pred_class = model.predict(X)[0]

    regime = "Bullish" if pred_class == 1 else "Bearish"
    signal = "Buy" if pred_class == 1 else "Sell"
    confidence = pred_prob[int(pred_class)] * 100

    return regime, signal, confidence