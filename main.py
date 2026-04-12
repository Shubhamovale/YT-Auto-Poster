import os
import json
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("YouTubeAutoPoster")

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/youtube.upload'
]

def get_credentials():
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not set. Please set it via GitHub Secrets.")
    
    creds_data = json.loads(creds_json)
    creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    return creds

def find_video_in_drive(drive_service, folder_id):
    logger.info(f"Searching for videos in Drive Folder: {folder_id}")
    query = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false"
    try:
        results = drive_service.files().list(
            q=query, pageSize=1, fields="nextPageToken, files(id, name)"
        ).execute()
        
        items = results.get('files', [])
        if not items:
            logger.info("No videos found in the specified Drive folder.")
            return None
        
        logger.info(f"Found video: {items[0]['name']}")
        return items[0]
    except Exception as e:
        logger.error(f"Error finding video in drive: {e}")
        raise

def download_video(drive_service, file_id, file_name):
    logger.info(f"Downloading {file_name} from Google Drive...")
    request = drive_service.files().get_media(fileId=file_id)
    with open(file_name, 'wb') as fh:
        response = request.execute()
        fh.write(response)
    logger.info(f"Download complete: {file_name}")

def upload_to_youtube(youtube_service, file_name):
    logger.info(f"Preparing to upload {file_name} to YouTube as a Public Short...")
    title = os.path.splitext(file_name)[0]
    
    body = {
        'snippet': {
            'title': title,
            'description': f"{title} #shorts",
            'tags': ['shorts'],
            'categoryId': '22'  # 22 is usually People & Blogs, you can change this
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(file_name, chunksize=-1, resumable=True)
    request = youtube_service.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    logger.info("Uploading step started. This may take a while depending on file size...")
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"Uploaded {int(status.progress() * 100)}%")
            
    video_id = response.get('id')
    logger.info(f"Upload Complete! Video ID: {video_id}")
    return video_id

def delete_from_drive(drive_service, file_id):
    logger.info(f"Deleting file {file_id} from Google Drive to avoid duplicate uploads...")
    drive_service.files().delete(fileId=file_id).execute()
    logger.info(f"Google Drive deletion successful.")

def main():
    try:
        folder_id = os.environ.get('DRIVE_FOLDER_ID')
        if not folder_id:
            raise ValueError("DRIVE_FOLDER_ID environment variable not set. Please set it via GitHub Secrets.")

        creds = get_credentials()
        
        # Build API clients
        drive_service = build('drive', 'v3', credentials=creds)
        youtube_service = build('youtube', 'v3', credentials=creds)
        
        # 1. Find a video to process
        video = find_video_in_drive(drive_service, folder_id)
        if not video:
            return  # No work to do
        
        file_id = video['id']
        file_name = video['name']
        
        # 2. Download the video locally
        download_video(drive_service, file_id, file_name)
        
        # 3. Upload to YouTube
        upload_to_youtube(youtube_service, file_name)
        
        # 4. Clean up local file
        if os.path.exists(file_name):
            os.remove(file_name)
            logger.info(f"Deleted temporary local file: {file_name}")
        
        # 5. Clean up from Google Drive
        delete_from_drive(drive_service, file_id)
        
        logger.info("All tasks completed successfully!")
        
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise

if __name__ == '__main__':
    main()
