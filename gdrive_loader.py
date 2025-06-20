import os
import base64
import json
import yaml
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def download_model(model_filename="model.json", folder_id=None):
    if os.path.exists(model_filename):
        print(f"✅ Model already exists locally: {model_filename}")
        return model_filename

    if folder_id is None:
        raise ValueError("❌ Google Drive folder ID is required.")

    try:
        print("🔐 Decoding service account credentials...")
        encoded = os.getenv("GDRIVE_CREDENTIALS_JSON")
        if not encoded:
            raise EnvironmentError("❌ GDRIVE_CREDENTIALS_JSON not found in environment.")

        creds_dict = json.loads(base64.b64decode(encoded).decode())

        # Write temporary settings.yaml
        settings = {
            "client_config_backend": "service",
            "service_config": creds_dict
        }
        with open("temp_settings.yaml", "w") as f:
            yaml.dump(settings, f)

        print("🔐 Authenticating with Google Drive...")
        gauth = GoogleAuth(settings_file="temp_settings.yaml")
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)

        print("🔍 Searching for model in Drive...")
        file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
        for file in file_list:
            if file['title'] == model_filename:
                print(f"📥 Downloading {model_filename} from Google Drive...")
                file.GetContentFile(model_filename)
                print("✅ Download complete")
                return model_filename

        raise FileNotFoundError(f"❌ '{model_filename}' not found in Drive folder: {folder_id}")

    except Exception as e:
        raise RuntimeError(f"❌ Failed to download model: {e}")
    finally:
        if os.path.exists("temp_settings.yaml"):
            os.remove("temp_settings.yaml")