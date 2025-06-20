import xgboost as xgb
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

# Train model
X, y = load_iris(return_X_y=True)
X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2)
model = xgb.XGBClassifier()
model.fit(X_train, y_train)
model.save_model("model.json")

# Upload to Google Drive
gauth = GoogleAuth()
gauth.LoadClientConfigFile("client_secrets.json")
gauth.LocalWebserverAuth() if os.getenv("CI") is None else gauth.CommandLineAuth()
drive = GoogleDrive(gauth)

file = drive.CreateFile({'title': 'model.json', 'parents': [{'id': os.environ["GDRIVE_FOLDER_ID"]}]})
file.SetContentFile("model.json")
file.Upload()
print("✅ model.json uploaded to Google Drive")