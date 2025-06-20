import os
import xgboost as xgb
import numpy as np
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def fetch_model_from_drive():
    print("📡 model.json not found locally. Fetching from Google Drive...")
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    # Search for the file by name
    file_list = drive.ListFile({'q': "title='model.json' and trashed=false"}).GetList()
    if file_list:
        file = file_list[0]
        file.GetContentFile('model.json')
        print("✅ model.json downloaded from Google Drive")
    else:
        raise FileNotFoundError("❌ model.json not found in Google Drive")

def generate_trade_signal(price_df, macro_df):
    if not os.path.exists("model.json"):
        fetch_model_from_drive()

    model = xgb.XGBClassifier()
    model.load_model("model.json")

    latest_macro = macro_df.iloc[-1]
    features = [
        latest_macro['inflation'],
        latest_macro['interest_rate'],
        latest_macro['gdp'],
        price_df['Close'].pct_change().rolling(5).mean().iloc[-1]
    ]

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