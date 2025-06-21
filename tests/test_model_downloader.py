import unittest
import os
from app import download_latest_model_for_ticker

class TestModelDownloader(unittest.TestCase):
    def test_download_model_file_for_ticker(self):
        folder_id = os.getenv("GDRIVE_FOLDER_ID")
        creds = os.getenv("GDRIVE_CREDENTIALS_JSON")

        self.assertIsNotNone(folder_id, "GDRIVE_FOLDER_ID is not set.")
        self.assertIsNotNone(creds, "GDRIVE_CREDENTIALS_JSON is not set.")

        model_name = download_latest_model_for_ticker("SPY", folder_id=folder_id)
        self.assertTrue(model_name.startswith("model_SPY_"))
        print(f"✅ Model download successful: {model_name}")

if __name__ == "__main__":
    unittest.main()