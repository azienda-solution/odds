from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


# Ajouter une permission d'éditeur pour le compte de service
def add_permission(file_id):
        # Créez le service Google Drive
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file('D:/Documents/Advanced-Python/ODDS/config/life-cm-f5238641f3f9.json', scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    email_account_service = 'life-942@life-cm.iam.gserviceaccount.com'  # Email du compte de service
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email_account_service
    }
    service.permissions().create(
        fileId=file_id,
        body=permission,
        fields='id'
    ).execute()
    print(f"Permission added for {email_account_service} on file {file_id}")

#add_permission('1tDs9qk37xVtEv5LVhqFlyWwgWmiHfeqW')
