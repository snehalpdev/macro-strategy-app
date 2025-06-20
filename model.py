import numpy as np
import xgboost as xgb

def generate_trade_signal(price_df, macro_df):
    # Combine features
    latest_macro = macro_df.iloc[-1]
    features = [
        latest_macro['inflation'],
        latest_macro['interest_rate'],
        latest_macro['gdp'],
        price_df['Close'].pct_change().rolling(5).mean().iloc[-1]
    ]

    model = xgb.XGBClassifier()
    model.load_model("model.json")  # You’d need to upload a trained model
    pred = model.predict_proba([features])[0]
    signal = "BUY" if pred[1] > 0.5 else "SELL"
    confidence = pred[1] * 100
    regime = detect_regime(latest_macro)

    return regime, signal, confidence

def detect_regime(row):
    if row['inflation'] > 0.03 and row['interest_rate'] > 0.03:
        return "Inflationary"
    elif row['gdp'] < 0:
        return "Recession"
    else:
        return "Expansion"