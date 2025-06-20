import pandas as pd
import numpy as np
import xgboost as xgb
from data import get_macro_data, get_price_data
from model import build_features
from utils import load_secrets
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

def upload_to_drive(filepath):
    gauth = GoogleAuth()
    gauth.LoadServiceConfigFile("service_account.json")
    gauth.ServiceAuth()
    drive = GoogleDrive(gauth)

    file = drive.CreateFile({
        'title': os.path.basename(filepath),
        'parents': [{'id': os.environ["GDRIVE_FOLDER_ID"]}]
    })
    file.SetContentFile(filepath)
    file.Upload()
    print(f"📤 Uploaded {filepath} to Google Drive")

def run_training_pipeline(ticker="SPY", lookback=180):
    secrets = load_secrets()
    fred_key = secrets.get("FRED_API_KEY")
    macro_df = get_macro_data(fred_key)
    price_df = get_price_data(ticker, lookback)

    if price_df.empty or macro_df.empty:
        raise ValueError("Could not retrieve data")

    df = price_df.copy()
    df["return"] = df["Close"].pct_change()
    df["volatility"] = df["Close"].rolling(10).std()
    df["momentum"] = df["Close"] - df["Close"].shift(10)
    df["target"] = np.where(df["Close"].shift(-1) > df["Close"], 1, 0)

    df = df.dropna()
    price_features = df[["return", "volatility", "momentum"]]
    macro_features = macro_df.select_dtypes(include=[np.number]).iloc[-len(price_features):].reset_index(drop=True)

    X = pd.concat([price_features.reset_index(drop=True), macro_features], axis=1)
    y = df["target"].reset_index(drop=True)

    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric="logloss")
    model.fit(X, y)

    model.save_model("model.json")
    upload_to_drive("model.json")
    return "✅ Model retrained and uploaded to Drive."