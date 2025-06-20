import xgboost as xgb
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

# Train model
X, y = load_iris(return_X_y=True)
X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2)
model = xgb.XGBClassifier()
model.fit(X_train, y_train)
model.save_model("model.json")

# Upload to Google Drive via service account
gauth = GoogleAuth()
gauth.LoadSettingsFile("settings.yml")  # <-- refers to your service config
gauth.ServiceAuth()                      # <-- key step for service accounts
drive = GoogleDrive(gauth)

file = drive.CreateFile({'title': 'model.json', 'parents': [{'id': os.environ["GDRIVE_FOLDER_ID"]}]})
file.SetContentFile("model.json")
file.Upload()
print("✅ model.json uploaded to Google Drive")