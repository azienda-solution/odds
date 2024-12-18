from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from test_perm import add_permission
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaFileUpload

def upload_file_to_drive(file_path, file_name, folder_id):
    """
    Uploads an Excel file to Google Drive and replaces it if it already exists.
    Creates the folder if it doesn't exist.

    Args:
        file_path (str): The local path to the Excel file.
        file_name (str): The name of the file on Google Drive.
        folder_id (str): The ID of the target folder on Google Drive.
    """
    try:
        # Authenticate using service account credentials
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('D:/Documents/Advanced-Python/ODDS/config/life-cm-f5238641f3f9.json', scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        # Check if the folder exists. If not, create it.
        folder_query = f"name = '{folder_id}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        folder_response = service.files().list(q=folder_query, fields="files(id, name)").execute()
        folders = folder_response.get('files', [])

        # If folder doesn't exist, create it
        if not folders:
            print(f"Folder with ID '{folder_id}' not found. Creating folder...")
            folder_metadata = {'name': 'My New Folder', 'mimeType': 'application/vnd.google-apps.folder'}
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder['id']
            print(f"Created folder with ID: {folder_id}")

        # Check if file already exists in the folder
        query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
        response = service.files().list(q=query, fields="files(id, name)").execute()
        files = response.get('files', [])

        # If file exists, delete it
        if files:
            print("File already exists. Replacing...")
            for file in files:
                service.files().delete(fileId=file['id']).execute()
                print(f"Deleted existing file: {file['name']} (ID: {file['id']})")

        # Upload the new file
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        print(f"Uploaded file successfully. File ID: {file.get('id')}")

    except Exception as e:
        print(f"An error occurred: {e}")




def upload_text_file_to_drive(folder_id, file_name):
    """
    Uploads a simple text file to a specific folder on Google Drive.
    
    Args:
        folder_id (str): The ID of the target folder on Google Drive.
        file_name (str): The name of the file to upload. Default is 'test.txt'.
        content (str): The content to write into the text file. Default is "This is a test file.".
    """
    try:
        # Authenticate using service account credentials
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('D:/Documents/Advanced-Python/ODDS/config/life-cm-f5238641f3f9.json', scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaFileUpload(file_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        print(f"File '{file_name}' uploaded successfully. File ID: {uploaded_file.get('id')}")
    
    except Exception as e:
        print(f"An error occurred: {e}")

# Exemple d'utilisation
#folder_id = '1iAwsrdawNPeww_FrSmB0AimH0Vzhz8L4'  # Remplacez par l'ID du dossier Google Drive où vous voulez uploader le fichier
#upload_text_file_to_drive(folder_id)

###############################################################
#upload_file_to_drive('games.xlsx', 'games.xlsx', "1iAwsrdawNPeww_FrSmB0AimH0Vzhz8L4")