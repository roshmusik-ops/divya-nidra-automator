import os
import sys
import json
import pickle
import argparse
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes needed for uploading to YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service(channel_name):
    """
    Authenticates the user and returns the YouTube API service.
    Uses a separate token file for each channel.
    """
    credentials = None
    token_file = f'token_{channel_name}.pickle'
    
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            credentials = pickle.load(token)
            
    # If there are no valid credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print(f"Refreshing access token for {channel_name}...")
            credentials.refresh(Request())
        else:
            print(f"Logging in to {channel_name}...")
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            # Run local server to capture the authorization code
            credentials = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
            
    return build('youtube', 'v3', credentials=credentials)

def initialize_upload(youtube, file_path, title, description, category_id="22", tags=None):
    """
    Initializes and executes the video upload to YouTube.
    """
    if tags is None:
        tags = ["shorts", "trending"]
        
    print(f"Preparing to upload {file_path}...")
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': 'public', # Set to public for automated shorts
            'selfDeclaredMadeForKids': False
        }
    }

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in bytes.
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
    )

    print("Uploading video...")
    response = None
    while response is None:
        status, response = insert_request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%.")

    print(f"Upload Complete! Video ID: {response['id']}")
    return response['id']

def find_video_to_upload(channel_name):
    """
    Finds the first .mp4 file in the channel's pending directory.
    """
    directory = f'videos_{channel_name}'
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}. Please place your videos here.")
        return None
        
    for file in os.listdir(directory):
        if file.endswith('.mp4'):
            return os.path.join(directory, file)
            
    print(f"No .mp4 files found in {directory}!")
    return None

def main():
    parser = argparse.ArgumentParser(description='Upload YouTube Shorts')
    parser.add_argument('--channel', required=True, help='Name of the channel (e.g., channel1 or channel2)')
    args = parser.parse_args()

    channel_name = args.channel
    print(f"Starting upload process for channel: {channel_name} at {datetime.now()}")

    if not os.path.exists('client_secrets.json'):
        print("ERROR: client_secrets.json not found! Please download your OAuth 2.0 Client IDs from Google Cloud Console and save it here.")
        sys.exit(1)

    # Authenticate FIRST so the user can log in during setup, even without videos
    try:
        youtube = get_authenticated_service(channel_name)
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    video_path = find_video_to_upload(channel_name)
    if not video_path:
        sys.exit(0)

    # Default fallback SEO
    title = os.path.splitext(os.path.basename(video_path))[0]
    title = f"{title} #shorts"
    description = f"{title}\n\nAutomated upload via Python."
    tags = ["shorts", "trending"]
    
    # Check for AI-generated SEO in seo_data.json
    seo_file = os.path.join(os.path.dirname(video_path), 'seo_data.json')
    if os.path.exists(seo_file):
        with open(seo_file, 'r') as f:
            seo_db = json.load(f)
            video_filename = os.path.basename(video_path)
            if video_filename in seo_db:
                data = seo_db[video_filename]
                title = data.get('title', title)
                description = data.get('description', description)
                tags = data.get('tags', tags)
                print(f"Loaded AI SEO Data for {video_filename}")

    # Automatically add Spotify promo to the top of every description
    promo_text = "✨ Subscribe for more peaceful moments and relaxation.\n\n"
    description = promo_text + description

    try:
        video_id = initialize_upload(youtube, video_path, title, description, tags=tags)
        
        # If running on GitHub Actions, just delete the file so it doesn't take up space in the repo.
        # Otherwise, move it to an uploaded folder locally.
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            os.remove(video_path)
            print(f"Deleted {video_path} from repository to save space.")
        else:
            uploaded_dir = f"uploaded_{channel_name}"
            if not os.path.exists(uploaded_dir):
                os.makedirs(uploaded_dir)
            os.rename(video_path, os.path.join(uploaded_dir, os.path.basename(video_path)))
            print(f"Moved {video_path} to {uploaded_dir}/")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
