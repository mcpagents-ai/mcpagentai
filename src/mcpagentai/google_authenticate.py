from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

def authenticate(pickle_file_path, credentials_json_path):
    creds = None
    # Load credentials from the token file if it exists
    if os.path.exists(pickle_file_path):
        with open(pickle_file_path, 'rb') as token:
            creds = pickle.load(token)

    # Authenticate if no valid credentials exist
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_json_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(pickle_file_path, 'wb') as token:
            pickle.dump(creds, token)

if __name__ == '__main__':
    authenticate("../../google_pickle.dump", "../../google_credentials.json")