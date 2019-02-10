import httplib2
from apiclient import discovery
import oauth2client as oauth
import os
from decouple import config, Csv


def credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    cred_path = os.path.abspath(config('GOOGLE_CREDENTIALS'))
    store = oauth.file.Storage(cred_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = oauth.client.flow_from_clientsecrets(
            config('GOOGLE_CLIENT_SECRETS'),
            config('GOOGLE_SCOPES', cast=Csv())
        )
        flow.user_agent = config('APP_NAME')
        credentials = oauth.tools.run_flow(flow, store, None)
        print('Storing credentials')
    return credentials


def build_creds(api='calendar', version='v3'):
    creds = credentials()
    http = creds.authorize(httplib2.Http())
    service = discovery.build(api, version, http=http)
    return creds, http, service


if __name__ == '__main__':
    print(credentials())
