import unittest
import os
import json
import numpy as np
from datetime import datetime

class TestSignalLogging(unittest.TestCase):
    def setUp(self):
        os.makedirs("logs", exist_ok=True)
        self.test_path = "logs/test_signal_log.jsonl"

    def test_signal_log_serialization(self):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "ticker": "TEST",
            "regime": "Neutral",
            "signal": "Hold",
            "confidence": np.float32(88.88),
            "price": np.float32(123.45)
        }

        # Ensure native Python floats
        entry["confidence"] = float(entry["confidence"])
        entry["price"] = float(entry["price"])

        with open(self.test_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        with open(self.test_path) as f:
            last_line = f.readlines()[-1]
            parsed = json.loads(last_line)
            self.assertIsInstance(parsed["confidence"], float)
            self.assertEqual(parsed["ticker"], "TEST")

    def tearDown(self):
        if os.path.exists(self.test_path):
            os.remove(self.test_path)