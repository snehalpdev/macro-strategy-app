import os
import requests
import xgboost as xgb

def download_model():
    file_id = "YOUR_FILE_ID"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    r = requests.get(url)
    with open("model.json", "wb") as f:
        f.write(r.content)

def load_model():
    if not os.path.exists("model.json"):
        download_model()
    model = xgb.XGBClassifier()
    model.load_model("model.json")
    return model