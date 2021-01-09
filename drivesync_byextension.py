from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import errors
from apiclient import http

#ammount = input('How many? \n')
ammount = 1000
downloaded = None

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']
sync_path = r"data\files"

def main():
    downloaded = 0
    totalsize = 0
    deletedfiles = 0
    creds = None
# CREDENTIALS AND LOGIN
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # SOLICITA PERMISSÃO CASO CREDENCEIAIS NÃO FOREM VALIDAS
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    # LISTA TODOS OS ARQUIVOS DO DRIVE
    results = service.files().list(
        pageSize=ammount, fields="nextPageToken, files(id, name, size)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            # VERIFICA SE É ARQUIVO OU PASTA
            try:
                sizeinmb = round(float(item['size']) / 1048576, 2)
                print(f"{item['name']}  [{sizeinmb} MegaBytes]")
                is_file = 1
            except:
                print(f"{item['name']}  [FOLDER]")
                is_file = 0

            ################ FUNCTIONS ###############

            # GET METADATA
            def print_file_metadata(service_metadata, file_id):
                try:
                    file = service_metadata.files().get(fileId=file_id).execute()
                    print('Title: %s' % file['name'])
                    print('MIME type: %s' % file['mimeType'])
                except errors.HttpError as error:
                    print('An error occurred: %s' % error)
            print_file_metadata(service, item['id'])
            # DOWNLOAD
            def download_file(service_download, file_id, local_fd):
                request = service_download.files().get_media(fileId=file_id)
                media_request = http.MediaIoBaseDownload(local_fd, request)
                while True:
                    try:
                        download_progress, done = media_request.next_chunk()
                    except errors.HttpError as error:
                        print('An error occurred: %s' % error)
                        return
                    if download_progress:
                        print('Download Progress: %d%%' % int(download_progress.progress() * 100))
                    if done:
                        print('Download Complete')
                        return
            # DELETE
            def delete_file(service_del, file_id):
                try:
                    service.files().delete(fileId=file_id).execute()
                except errors.HttpError as error:
                    print('An error occurred: %s' % error)

            # GET FILE EXTENSION
            split = str(item['name']).split('.')
            try:
                file_verify = split[1]
                #have_extension = 1
                type = f'{sync_path}\\{split[-1]}'
            except:
                have_extension = 0
                type = f'{sync_path}\\NOEXTENSION'

            file = f"{type}\\{item['name']}"
            if os.path.exists(type):
                #print(f'Pasta de arquivos {type} já existe!')
                pathfile = file
            else:
                print(f'Folder {type} doesnt exists, creating...\n')
                os.mkdir(type)
                pathfile = file

            # DOWNLOAD ALL FILES
            if is_file == 1:
                if os.path.exists(pathfile):
                    localfile = open(pathfile, 'r')
                    localfile.seek(0, 2)
                    localsize = int(localfile.tell())
                    remotesize = int(item['size'])

                    # IGNORE EXISTING FILES
                    print(f'Local file size: {localsize} bytes / Remote file size: {remotesize} bytes')
                    if localsize == remotesize:
                        print(f"File {item['name']} already exists with same size, ignoring and deleting remote file...\n")
                        delete_file(service, item['id'])
                        deletedfiles += 1
                    else:
                        # DOWNLOAD INCOMPLETE FILES
                        if localsize == 0:
                            print(f"File {item['name']} already exists with different size, downloading...\n")
                            filedownload = open(pathfile, 'wb')
                            #print(f"Downloading {item['name']}...")
                            try:
                                download_file(service, item['id'], filedownload)
                                downloaded += 1
                                print(f"Deleting {item['name']}...\n")
                                delete_file(service, item['id'])
                            except:
                                print('Erro ao baixar')
                else:
                    filedownload = open(pathfile, 'wb')
                    #print(f"Downloading {item['name']}...")
                    try:
                        download_file(service, item['id'], filedownload)
                        print(f"Deleting {item['name']}...\n")
                        delete_file(service, item['id'])
                    except:
                        print('Erro ao baixar')

                    remotesize = int(item['size'])
                    downloaded += 1
                    totalsize += remotesize
                    print(f'File: {downloaded}/{ammount}\n\n')

    totalsizeinmb = round(float(totalsize) / 1048576, 2)
    print(f'\nTotal files downloaded: {downloaded} ({totalsizeinmb}MB)')
    #print(f'Total files ignored: {deletedfiles}')
if __name__ == '__main__':
    main()

input('Enter para finalizar')