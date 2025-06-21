# 📈 Market Forecasting ML Pipeline + Streamlit App

This repository provides a complete pipeline for building and serving a financial classification model. It includes:

- 🧠 Weekly model retraining using macroeconomic + market data
- 📤 Secure model upload to Google Drive with versioning + cleanup
- 🎯 Interactive prediction app powered by Streamlit

---

## 🚀 Features

- ✅ Model trains weekly via GitHub Actions
- ✅ Authenticates to Google Drive using a base64-encoded service account
- ✅ Automatically uploads a timestamped model file
- ✅ Keeps only the latest N model versions (e.g. last 5)
- ✅ Easily configurable secrets + local override support
- ✅ Lightweight Streamlit app for running predictions

---

## 📁 Project Structure


. ├── train_pipeline.py          # Main training + upload script ├── app.py                     # Streamlit app for model inference ├── data/                      # Data fetching logic ├── model/                     # Feature engineering + model utils ├── utils.py                   # Secret loading + helper functions ├── requirements.txt ├── .github/workflows/train.yml └── README.md

---

## 🧠 Model Training

The model is an `XGBoost` binary classifier that combines macroeconomic indicators (via FRED) with market technical signals to predict whether the asset will close higher tomorrow.

Training pipeline includes:

- Price data: return, volatility, momentum
- Macroeconomic features: selected FRED indicators
- `model.json` export after training
- Auto-upload to Google Drive (via API)
- Cleanup of older model files

Run locally with:

```bash
export FRED_API_KEY=your_key
export GDRIVE_FOLDER_ID=your_drive_folder_id
export GDRIVE_CREDENTIALS_JSON=base64_encoded_service_account_json

python train_pipeline.py



🌐 Streamlit App
The app.py file loads the most recent model and allows you to test predictions with current or hypothetical inputs. Just run:
streamlit run app.py


App features:
- Input sliders for return, volatility, momentum
- Auto-detection of model file from Drive (or fallback to local)
- Display of class prediction probabilities

🔐 Required Secrets (GitHub + Local)
Whether running locally or in GitHub Actions, you'll need these environment variables:
| Key | Description | 
| FRED_API_KEY | API key for fetching macroeconomic indicators | 
| GDRIVE_FOLDER_ID | Google Drive folder ID for uploading models | 
| GDRIVE_CREDENTIALS_JSON | Base64-encoded Google service account credentials | 


In GitHub, set these under:
Settings → Secrets and variables → Actions → Repository secrets
To encode your service account JSON for GitHub:
base64 service_account.json



🛠 GitHub Actions
This repository includes a scheduled retraining workflow:
name: Weekly Model Retrain + Drive Upload

on:
  schedule:
    - cron: "0 3 * * 0"  # Sundays @ 03:00 UTC
  workflow_dispatch:


To manually trigger a run, visit the GitHub Actions tab and click Run workflow.

📂 Model File Naming + Cleanup
Every upload to Drive is timestamped like:
model_20250721_145055.json


To reduce clutter, only the most recent 5 versions are retained — older models are deleted automatically via the pipeline.

📊 Example Output (from Streamlit App)
Input: return=0.0031, volatility=0.0164, momentum=1.27
Prediction:
⬆️ Chance of upward move tomorrow: 64.2%
⬇️ Chance of downward move: 35.8%



✅ Workflow Status
Model Training

📝 License
MIT — you’re free to use and remix with attribution.
