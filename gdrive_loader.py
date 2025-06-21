from google.oauth2 import service_account
from googleapiclient.discovery import build
import base64
import json
import os

def download_model_from_drive(model_filename, folder_id):
    encoded = os.getenv("GDRIVE_CREDENTIALS_JSON")
    if not encoded:
        raise EnvironmentError("Missing GDRIVE_CREDENTIALS_JSON")

    creds_dict = json.loads(base64.b64decode(encoded).decode())
    creds = service_account.Credentials.from_service_account_info(creds_dict)
    service = build("drive", "v3", credentials=creds)

    # Search for the file
    query = f"'{folder_id}' in parents and trashed = false and name = '{model_filename}'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        raise FileNotFoundError(f"'{model_filename}' not found in folder {folder_id}")

    file_id = files[0]["id"]
    request = service.files().get_media(fileId=file_id)
    with open(model_filename, "wb") as f:
        downloader = build("drive", "v3", credentials=creds).files().get_media(fileId=file_id)
        f.write(request.execute())

    print(f"✅ Downloaded '{model_filename}'")
