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
    # REQUIRE LOGIN IF CREDENTIAL EXPIRES
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

    # COUNT ALL FILES
    results_count = service.files().list(q=f"mimeType!='application/vnd.google-apps.folder' ",
                                   pageSize=ammount, fields="nextPageToken, files(id, name, size)").execute()
    counts = results_count.get('files', [])
    alltotalsize = 0
    for count in counts:
        countsize = int(count['size'])
        alltotalsize += countsize
    total = len(counts)

    print(f'{total} files found, {round(float(alltotalsize) / 1048576, 2)}MB')




    # LIST ALL FOLDERS
    folder_results = service.files().list(q="mimeType='application/vnd.google-apps.folder'",
        pageSize=ammount, fields="nextPageToken, files(id, name)").execute()
    folders = folder_results.get('files', [])

    if not folders:
        print('No folder found.')
    else:
        print('Folders:')
        for folder in folders:
            print(f"{folder['name']}")

            # LIST ALL FILES IN FOLDER
            results = service.files().list(q=f"mimeType!='application/vnd.google-apps.folder' andparents in '{folder['id']}' ", pageSize=ammount, fields="nextPageToken, files(id, name, size)").execute()
            items = results.get('files', [])
            if not items:
                print('------ No file found')
            else:
                path = f"{sync_path}\\{folder['name']}"
                if os.path.exists(path):
                    print('')
                else:
                    # print(f'Folder {path} doesnt exists, creating...\n')
                    os.mkdir(path)
                # print(path)

                #print('Files:\n')
                for item in items:
                    print(f"------ ID: {item['id']} | Filename: {item['name']}")
                    file = f"{path}\\{item['name']}"
                    pathfile = file

                    # DOWNLOAD ALL FILES
                    if os.path.exists(pathfile):
                        localfile = open(pathfile, 'r')
                        localfile.seek(0, 2)
                        localsize = int(localfile.tell())
                        remotesize = int(item['size'])

                        # IGNORE EXISTING FILES
                        print(f'Local file size: {localsize} bytes / Remote file size: {remotesize} bytes')
                        if localsize == remotesize:
                            print(
                                f"File {item['name']} already exists with same size, ignoring and deleting remote file...\n")
                            delete_file(service, item['id'])
                            deletedfiles += 1
                        else:
                            # DOWNLOAD INCOMPLETE FILES
                            if localsize == 0:
                                print(f"File {item['name']} already exists with different size, downloading...\n")
                                filedownload = open(pathfile, 'wb')
                                # print(f"Downloading {item['name']}...")
                                try:
                                    download_file(service, item['id'], filedownload)
                                    downloaded += 1
                                    print(f"Deleting {item['name']}...\n")
                                    delete_file(service, item['id'])
                                except:
                                    print('Erro ao baixar')
                    else:
                        filedownload = open(pathfile, 'wb')
                        # print(f"Downloading {item['name']}...")
                        try:
                            download_file(service, item['id'], filedownload)
                            print(f"Deleting {item['name']}...")
                            delete_file(service, item['id'])
                        except:
                            print('Error')

                        remotesize = int(item['size'])
                        downloaded += 1
                        totalsize += remotesize
                        print(f'{downloaded}/{total}')
                        percent = totalsize / alltotalsize * 100
                        print(f'Total: {round(float(totalsize) / 1048576, 2)}MB of {round(float(alltotalsize) / 1048576, 2)}MB downloaded ({round(float(percent), 2)}%)\n\n')

    totalsizeinmb = round(float(totalsize) / 1048576, 2)
    print(f'\nTotal files downloaded: {downloaded} ({totalsizeinmb}MB)')
    #print(f'Total files ignored: {deletedfiles}')
if __name__ == '__main__':
    main()

input('Enter to finish')