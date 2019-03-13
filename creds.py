import os.path
import pickle

from googleapiclient.discovery import build, Resource
from googleapiclient import discovery_cache
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from decouple import config, Csv


DEFAULT_PICKLE_FILE = config('GOOGLE_TOKEN_PICKLE', default='token.pickle')

def credentials(pickle_file: str = DEFAULT_PICKLE_FILE) -> Credentials:
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
            flow = InstalledAppFlow.from_client_secrets_file(
                config('GOOGLE_CLIENT_SECRETS'),
                config('GOOGLE_SCOPES', cast=Csv()))
            flow.user_agent = config('APP_NAME')
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open(pickle_file, 'wb') as token:
            pickle.dump(creds, token)
    return creds


def build_service(api, version, creds: Credentials = None) -> Resource:
    if creds is None:
        creds = credentials()
    return build(api, version, credentials=creds)


def build_calendar(version='v3') -> Resource:
    return build_service('calendar', version)


def build_gmail(version='v1') -> Resource:
    return build_service('gmail', version)


if __name__ == '__main__':
    print(credentials())
