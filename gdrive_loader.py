from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

def download_model(model_filename="model.json", folder_id=None, credentials_path="service_account.json"):
    if os.path.exists(model_filename):
        print(f"✅ Model already exists locally: {model_filename}")
        return model_filename

    if folder_id is None:
        raise ValueError("Google Drive folder ID is required.")

    try:
        print("🔐 Authenticating with Google Drive...")
        gauth = GoogleAuth()
        gauth.LoadServiceConfigFile(credentials_path)
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)

        file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
        for file in file_list:
            if file['title'] == model_filename:
                print(f"📥 Downloading {model_filename} from Google Drive...")
                file.GetContentFile(model_filename)
                return model_filename

        raise FileNotFoundError(f"❌ {model_filename} not found in Drive folder {folder_id}")

    except Exception as e:
        raise RuntimeError(f"❌ Failed to download model: {e}")