import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the token you generated.
SCOPES = [
    'https://www.googleapis.com/auth/drive',            # Read and delete files in Drive
    'https://www.googleapis.com/auth/youtube.upload'    # Upload YouTube videos
]

def main():
    """Shows basic usage of the Drive API and YouTube API.
    Guides the user to generate an OAuth refresh token.
    """
    if not os.path.exists('client_secret.json'):
        print("-----------------\n")
        print("ERROR: client_secret.json not found!\n")
        print("Please follow these steps:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create a Project and enable 'YouTube Data API v3' and 'Google Drive API'")
        print("3. Go to API & Services -> Credentials -> Create Credentials -> OAuth client ID")
        print("4. Select 'Desktop App' as the application type")
        print("5. Download the JSON file and rename it to 'client_secret.json' in this folder")
        print("-----------------\n")
        return

    # Create the flow using the client secrets file from the Google API Console.
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)

    # Convert credentials to a dictionary
    creds_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

    # Save to JSON string for easy copy-pasting to GitHub Secrets
    creds_json = json.dumps(creds_data)
    
    with open('token.json', 'w') as f:
        f.write(creds_json)

    print("\n--- ATTENTION ---")
    print("Authentication successful!")
    print("Your tokens have been saved to 'token.json'.")
    print("Open 'token.json' and copy its ENTIRE content.")
    print("Then go to your GitHub Repository -> Settings -> Secrets and variables -> Actions")
    print("Create a New repository secret named: GOOGLE_CREDENTIALS")
    print("Paste the entire content of 'token.json' into the Secret value.")
    print("-----------------\n")

if __name__ == '__main__':
    main()
