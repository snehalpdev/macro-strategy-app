# 🤝 Contributing to Macro Strategy Dashboard

Thanks for jumping in! This project welcomes clean code, fresh ideas, and macro market nerds.

---

## 📦 Environment Setup

```bash
git clone https://github.com/YOUR_USERNAME/macro-strategy-dashboard.git
cd macro-strategy-dashboard
pip install -r requirements.txt


Create a .env file (or export env vars in your CI):
GDRIVE_FOLDER_ID=your_drive_folder_id
GDRIVE_CREDENTIALS_JSON=base64_encoded_json
FRED_API_KEY=your_fred_key



🧪 Local Testing
All tests live in /tests/. To run everything:
python -m unittest discover -s tests


Test coverage includes:
- ✅ Signal logger (test_logging.py)
- ✅ Model trainer (test_train_pipeline.py)
- ✅ Drive model loader (test_model_downloader.py)
Tests are automatically run on GitHub Actions on every push to main.

📬 Contribution Guidelines
- Open a branch from main: feature/your-change
- If you’re adding functionality, add a test for it
- Format with black or ruff (optional but welcome)
- Open a pull request — I review quickly and kindly!

💡 Questions?
File an issue, open a PR, or ping me in the repo. Let’s build something great 🚀

