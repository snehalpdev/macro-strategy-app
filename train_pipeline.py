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
    encoded = os.getenv("GDRIVE_CREDENTIALS_JSON")
    if not encoded:
        raise EnvironmentError("❌ Missing GDRIVE_CREDENTIALS_JSON")
    creds_dict = json.loads(base64.b64decode(encoded).decode())
    creds = service_account.Credentials.from_service_account_info(creds_dict)
    return build("drive", "v3", credentials=creds)

def upload_to_drive(filepath, retries=3, timestamp_version=True):
    service = get_drive_service()
    filename = os.path.basename(filepath)

    if timestamp_version:
        name_root, ext = os.path.splitext(filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{name_root}_{timestamp}{ext}"

    file_metadata = {
        'name': filename,
        'parents': [os.environ["GDRIVE_FOLDER_ID"]]
    }
    media = MediaFileUpload(filepath, resumable=True)

    for attempt in range(1, retries + 1):
        try:
            uploaded = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print(f"📤 Uploaded {filename} to Drive (file ID: {uploaded.get('id')})")
            cleanup_old_models(os.environ["GDRIVE_FOLDER_ID"])
            return
        except HttpError as e:
            print(f"⚠️ Upload attempt {attempt} failed: {e}")
            time.sleep(2 * attempt)

    raise RuntimeError(f"❌ Failed to upload after {retries} retries.")

def cleanup_old_models(folder_id, prefix="model_", max_versions=5):
    service = get_drive_service()
    query = f"'{folder_id}' in parents and trashed = false and name contains '{prefix}'"
    results = service.files().list(q=query, fields="files(id, name, createdTime)").execute()
    files = results.get("files", [])
    if len(files) <= max_versions:
        return

    files.sort(key=lambda x: x["createdTime"])
    old_files = files[:-max_versions]
    for file in old_files:
        service.files().delete(fileId=file["id"]).execute()
        print(f"🗑️ Deleted old model: {file['name']}")

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

    model.save_model("model.json")
    upload_to_drive("model.json")
    return "✅ Model retrained and uploaded to Drive."