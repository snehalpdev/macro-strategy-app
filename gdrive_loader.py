import os
import base64
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def get_drive_credentials_from_env(env_var="GDRIVE_CREDENTIALS_JSON", temp_file="temp_service_account.json"):
    encoded = os.getenv(env_var)
    if not encoded:
        raise EnvironmentError(f"❌ Environment variable '{env_var}' not found.")
    decoded = base64.b64decode(encoded).decode()
    with open(temp_file, "w") as f:
        f.write(decoded)
    return temp_file

def download_model(model_filename="model.json", folder_id=None):
    if os.path.exists(model_filename):
        print(f"✅ Model already exists locally: {model_filename}")
        return model_filename

    if folder_id is None:
        raise ValueError("❌ Google Drive folder ID is required.")

    try:
        print("🔐 Authenticating with service account via GDRIVE_CREDENTIALS_JSON...")
        credentials_path = get_drive_credentials_from_env()
        gauth = GoogleAuth()
        gauth.credentials = gauth.LoadServiceAccountFile(credentials_path)
        drive = GoogleDrive(gauth)

        # Search for the model file in the specified folder
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
        # Optional cleanup
        if os.path.exists("temp_service_account.json"):
            os.remove("temp_service_account.json")