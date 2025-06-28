import time
import subprocess
import os
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_google_drive_service():
    """Gets Google Drive service with proper authentication."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
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

    return build('drive', 'v3', credentials=creds)

def upload_to_drive(file_path, folder_id=None):
    """Uploads a file to Google Drive.
    Args:
        file_path: Path to the file to upload
        folder_id: Optional Google Drive folder ID to upload to
    Returns:
        File ID of the uploaded file
    """
    try:
        service = get_google_drive_service()
        file_metadata = {
            'name': os.path.basename(file_path),
        }
        if folder_id:
            file_metadata['parents'] = [folder_id]
            
        media = MediaFileUpload(
            file_path,
            mimetype='audio/mpeg',
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"File uploaded successfully. File ID: {file.get('id')}")
        return file.get('id')
    except Exception as e:
        print(f"An error occurred while uploading to Google Drive: {e}")
        return None

def delete_local_file(file_path):
    """Deletes a local file.
    Args:
        file_path: Path to the file to delete
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        os.remove(file_path)
        print(f"Successfully deleted local file: {file_path}")
        return True
    except Exception as e:
        print(f"Error deleting local file {file_path}: {e}")
        return False

# Create recordings directory if it doesn't exist
recordings_dir = "recordings"
os.makedirs(recordings_dir, exist_ok=True)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Record KBS 1FM stream')
parser.add_argument('--duration', type=int, default=7200,
                   help='Recording duration in seconds (default: 7200 seconds / 2 hours)')
parser.add_argument('--url', type=str, 
                   default='https://onair.kbs.co.kr/index.html?sname=onair&stype=live&ch_code=24&ch_type=radioList&bora=off&chat=off',
                   help='URL of the stream (default: KBS 1FM)')
parser.add_argument('--upload', action='store_true',
                   help='Enable upload to Google Drive and automatically delete local file. To use this, you need to set up Google Drive API first. (default: False)')
parser.add_argument('--ffmpeg', type=str, default='ffmpeg')

args = parser.parse_args()

# Setup Selenium for headless Chrome on macOS
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

# Navigate to the specified URL
print(f"Navigating to: {args.url}")
driver.get(args.url)

try:
    # Wait for JWPlayer to initialize and extract stream URL
    print("Waiting for stream to load...")
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return typeof jwplayer === 'function' && jwplayer('kbs-social-player').getPlaylistItem() != null")
    )

    stream_url = driver.execute_script("return jwplayer('kbs-social-player').getPlaylistItem().file;")
    print("Stream URL obtained:", stream_url)

    # Generate filename with current datetime
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(recordings_dir, f"kbs_1fm_{current_time}.mp3")
    duration_seconds = args.duration  # Get duration from command line argument
    print(f"Starting recording to {output_file} for {duration_seconds/3600:.1f} hours...")

    ffmpeg_bin_path = os.path.abspath(os.path.expanduser(args.ffmpeg))
    ffmpeg_cmd = [
        f'{ffmpeg_bin_path}',
        "-loglevel", "warning",  # Reduce output verbosity
        "-i", stream_url,
        "-ac", "1",         # Mono
        "-ar", "32000",     # 32kHz sample rate
        "-c:a", "libmp3lame",
        "-q:a", "4",
        "-t", str(duration_seconds),
        output_file
    ]
    subprocess.run(ffmpeg_cmd)
    
    # Upload the recorded file to Google Drive only if --upload flag is set
    if args.upload:
        print("Uploading recording to Google Drive...")
        file_id = upload_to_drive(output_file)
        if file_id:
            print("Upload successful, deleting local file...")
            delete_local_file(output_file)
    else:
        print("Google Drive upload is disabled. Recording saved locally only.")

except Exception as e:
    print("Error occurred:", e)
finally:
    driver.quit()
