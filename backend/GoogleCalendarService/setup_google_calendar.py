"""
Script to set up Google Calendar API credentials
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def setup_google_calendar():
    """Set up Google Calendar API credentials"""
    
    print("🔧 Setting up Google Calendar API...")
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("📝 Please follow these steps:")
        print("1. Go to https://console.developers.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Calendar API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Download the JSON file and rename it to 'credentials.json'")
        print("6. Place it in this directory")
        return False
    
    creds = None
    
    # Check if token.json exists
    if os.path.exists('token.json'):
        print("📄 Loading existing token...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Please log in to Google...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        print("💾 Saving credentials...")
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    # Test the API
    try:
        print("🧪 Testing Google Calendar API...")
        service = build('calendar', 'v3', credentials=creds)
        
        # Call the Calendar API
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                            maxResults=10, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        print(f"✅ Google Calendar API working! Found {len(events)} events")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Google Calendar API: {e}")
        return False

if __name__ == "__main__":
    from datetime import datetime
    setup_google_calendar()
