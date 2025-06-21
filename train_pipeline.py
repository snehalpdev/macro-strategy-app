import os
import io
import json
import base64
import time
import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from data import get_macro_data, get_price_data
from model import build_features
from utils import load_secrets

def get_drive_service():
    creds_json = os.getenv("GDRIVE_CREDENTIALS_JSON")
    if not creds_json:
        raise EnvironmentError("Missing GDRIVE_CREDENTIALS_JSON")
    creds_dict = json.loads(base64.b64decode(creds_json).decode())
    creds = service_account.Credentials.from_service_account_info(creds_dict)
    return build("drive", "v3", credentials=creds)

def upload_to_drive(filepath, ticker, retries=3):
    service = get_drive_service()
    name_root = f"model_{ticker.upper()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    file_metadata = {
        'name': name_root,
        'parents': [os.environ["GDRIVE_FOLDER_ID"]],
    }
    media = MediaFileUpload(filepath, resumable=True)

    for attempt in range(retries):
        try:
            uploaded = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print(f"📤 Uploaded: {name_root}")
            cleanup_old_models(ticker=ticker, folder_id=os.environ["GDRIVE_FOLDER_ID"])
            return
        except HttpError as e:
            print(f"⚠️ Upload attempt {attempt+1} failed: {e}")
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("Upload failed after multiple attempts")

def cleanup_old_models(ticker, folder_id, max_versions=5):
    service = get_drive_service()
    prefix = f"model_{ticker.upper()}_"
    query = f"'{folder_id}' in parents and trashed = false and name contains '{prefix}'"
    files = service.files().list(q=query, fields="files(id, name, createdTime)").execute().get("files", [])
    if len(files) <= max_versions:
        return
    files.sort(key=lambda f: f["createdTime"])
    for old in files[:-max_versions]:
        service.files().delete(fileId=old["id"]).execute()
        print(f"🗑️ Deleted old model: {old['name']}")

def run_training_pipeline(ticker="SPY", lookback=180):
    secrets = load_secrets()
    fred_key = secrets.get("FRED_API_KEY")
    macro_df = get_macro_data(fred_key)
    price_df = get_price_data(ticker, lookback)

    if price_df.empty or macro_df.empty:
        raise ValueError("❌ Could not retrieve data")

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

    model_path = "model.json"
    model.save_model(model_path)
    upload_to_drive(model_path, ticker)
    return f"✅ Retrained model for {ticker} uploaded to Drive."