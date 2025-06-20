# 📈 Macro-Aware Trading Dashboard

An interactive Streamlit dashboard that blends macroeconomic signals and technical price indicators using machine learning to generate real-time trade signals — complete with retraining, explainability, performance tracking, GitHub Actions automation, and branded PDF reports.

---

## 🚀 Features

- 💹 Real-time trade signal generator powered by XGBoost
- 📊 Combines macroeconomic and technical indicators
- 🔁 Manual model retraining or via GitHub Actions
- 📬 Email alerts on high-confidence signals (optional)
- 🧠 SHAP model explainability support
- 📜 Signal history log with filtering
- 📈 Strategy vs Buy & Hold equity curve
- 📄 Branded PDF strategy reports (with cover, metrics, charts)
- ☁️ Secure Google Drive model upload integration
- 🌑 Fully themed dark UI with responsive layout

---

## 📷 Preview

> _Insert screenshots here showing the dashboard, signal chart, and PDF export_

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/macro-strategy-dashboard.git
cd macro-strategy-dashboard
pip install -r requirements.txt

2. Configure Secrets
Option A: .env (for local CLI scripts)
Create a .env file

FRED_API_KEY=your_fred_api_key
GDRIVE_FOLDER_ID=your_google_drive_folder_id
EMAIL_USERNAME=you@example.com           # optional
EMAIL_PASSWORD=your_email_password       # optional

Option B: secrets.toml (for Streamlit)
Create .streamlit/secrets.toml:

FRED_API_KEY = "your_fred_api_key"
GDRIVE_FOLDER_ID = "your_google_drive_folder_id"

Absolutely — here’s your complete, ready-to-copy README.md file:
# 📈 Macro-Aware Trading Dashboard

An interactive Streamlit dashboard that blends macroeconomic signals and technical price indicators using machine learning to generate real-time trade signals — complete with retraining, explainability, performance tracking, GitHub Actions automation, and branded PDF reports.

---

## 🚀 Features

- 💹 Real-time trade signal generator powered by XGBoost
- 📊 Combines macroeconomic and technical indicators
- 🔁 Manual model retraining or via GitHub Actions
- 📬 Email alerts on high-confidence signals (optional)
- 🧠 SHAP model explainability support
- 📜 Signal history log with filtering
- 📈 Strategy vs Buy & Hold equity curve
- 📄 Branded PDF strategy reports (with cover, metrics, charts)
- ☁️ Secure Google Drive model upload integration
- 🌑 Fully themed dark UI with responsive layout

---

## 📷 Preview

> _Insert screenshots here showing the dashboard, signal chart, and PDF export_

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/macro-strategy-dashboard.git
cd macro-strategy-dashboard
pip install -r requirements.txt


2. Configure Secrets
Option A: .env (for local CLI scripts)
Create a .env file:
FRED_API_KEY=your_fred_api_key
GDRIVE_FOLDER_ID=your_google_drive_folder_id
EMAIL_USERNAME=you@example.com           # optional
EMAIL_PASSWORD=your_email_password       # optional


Option B: secrets.toml (for Streamlit)
Create .streamlit/secrets.toml:
FRED_API_KEY = "your_fred_api_key"
GDRIVE_FOLDER_ID = "your_google_drive_folder_id"


3. Set Up Google Drive Integration
- Create a service account on Google Cloud
- Share your target Drive folder with the service account email
- Download service_account.json
- Base64 encode it for GitHub Actions:
base64 service_account.json > encoded.txt



▶️ Run the App
streamlit run app.py


Then open: http://localhost:8501

🔁 GitHub Actions: Weekly Retraining
A workflow at .github/workflows/retrain_and_upload.yml retrains the model and uploads it weekly to Drive.
Set the following GitHub secrets:
- FRED_API_KEY
- GDRIVE_FOLDER_ID
- GDRIVE_CREDENTIALS_JSON (base64-encoded service_account.json)

📁 Project Structure
macro-strategy-dashboard/
├── app.py                      # Main Streamlit dashboard
├── model.py                    # Model loading and signal logic
├── data.py                     # Macro + price data loaders
├── train_pipeline.py           # Training + Drive upload pipeline
├── utils.py                    # Secrets loader
├── alerts.py                   # Email alerts (optional)
├── report_generator.py         # PDF report generation
├── logs/                       # Generated signal logs (jsonl)
├── .streamlit/
│   ├── config.toml             # UI theming
│   └── secrets.toml            # Streamlit secrets (optional)
├── .env                        # Environment variables (gitignored)
├── .env.template               # Sample for environment setup
├── requirements.txt            # Project dependencies
└── .github/
    └── workflows/
        └── retrain_and_upload.yml



🧪 Dependencies
- streamlit, xgboost, shap, pandas, pdfkit, matplotlib, scikit-learn
- External tools: wkhtmltopdf (required for PDF generation)
- Gmail SMTP or similar for alerts (optional)

📬 Contributions
PRs and feature suggestions are welcome! Fork, clone, and build better trading tools together 📈

🛡 License
MIT

🙏 Acknowledgments
- FRED API
- Streamlit
- SHAP
- PyDrive2


