import unittest
import os
from train_pipeline import run_training_pipeline

class TestTrainingPipeline(unittest.TestCase):
    def test_run_training_returns_success(self):
        folder_id = os.getenv("GDRIVE_FOLDER_ID")
        creds = os.getenv("GDRIVE_CREDENTIALS_JSON")

        self.assertIsNotNone(folder_id, "GDRIVE_FOLDER_ID is not set.")
        self.assertIsNotNone(creds, "GDRIVE_CREDENTIALS_JSON is not set.")

        result = run_training_pipeline(ticker="SPY", lookback=30)
        self.assertIn("✅", result)
        print("✅ Training pipeline returned success message.")

if __name__ == "__main__":
    unittest.main()