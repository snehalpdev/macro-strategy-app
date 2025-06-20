import os
import base64
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def get_drive_settings_from_env(env_var="GDRIVE_CREDENTIALS_JSON"):
    encoded = os.getenv(env_var)
    if not encoded:
        raise EnvironmentError(f"❌ Environment variable '{env_var}' not found.")
    decoded = base64.b64decode(encoded).decode()
    creds_dict = json.loads(decoded)

    # Write to a temporary settings file
    settings = {
        "client_config_backend": "service",
        "service_config": {
            "client_email": creds_dict["client_email"],
            "client_id": creds_dict["client_id"],
            "private_key": creds_dict["private_key"],
            "private_key_id": creds_dict["private_key_id"],
            "type": creds_dict["type"],
        }
    }

    with open("temp_settings.yaml", "w") as f:
        import yaml
        yaml.dump(settings, f)

    return "temp_settings.yaml"

def download_model(model_filename="model.json", folder_id=None):
    if os.path.exists(model_filename):
        print(f"✅ Model already exists locally: {model_filename}")
        return model_filename

    if folder_id is None:
        raise ValueError("❌ Google Drive folder ID is required.")

    try:
        print("🔐 Authenticating with service account via GDRIVE_CREDENTIALS_JSON...")
        settings_path = get_drive_settings_from_env()
        gauth = GoogleAuth(settings_file=settings_path)
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)

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