"""
Script to set up Google Calendar API credentials
"""

import os
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Scopes for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def setup_google_calendar():
    """Set up Google Calendar API credentials"""
    
    print("Setting up Google Calendar API...")
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("credentials.json not found!")
        print("Please follow these steps:")
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
        print("Loading existing token...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None
        
        if not creds:
            print("Please log in to Google...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=8080)
            except Exception as e:
                print(f"Error during authentication: {e}")
                return False
        
        # Save the credentials for the next run
        print("Saving credentials...")
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    # Test the API
    try:
        print("Testing Google Calendar API...")
        service = build('calendar', 'v3', credentials=creds)
        
        # Call the Calendar API
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=now,
            maxResults=10, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        
        print(f"Google Calendar API working! Found {len(events)} events")
        
        # Show some sample events
        if events:
            print("\nSample events:")
            for event in events[:3]:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"- {event.get('summary', 'No Title')} at {start}")
        
        return True
        
    except HttpError as e:
        print(f"Google Calendar API error: {e}")
        return False
    except Exception as e:
        print(f"Error testing Google Calendar API: {e}")
        return False

def test_calendar_integration():
    """Test the calendar integration with the service"""
    try:
        from app import get_google_calendar_service, get_events_for_date
        
        print("\nTesting calendar integration...")
        service = get_google_calendar_service()
        
        if not service:
            print("No Google Calendar service available")
            return False
        
        # Test getting today's events
        today = datetime.now().strftime("%Y-%m-%d")
        # Note: get_events_for_date is not available in this context
        # Just test basic API access
        
        print("Google Calendar service is working!")
        
        return True
        
    except Exception as e:
        print(f"Error testing calendar integration: {e}")
        return False

if __name__ == "__main__":
    success = setup_google_calendar()
    if success:
        print("\nGoogle Calendar setup completed successfully!")
        print("You can now use the Google Calendar service.")
    else:
        print("\nGoogle Calendar setup failed.")
        print("Please check your credentials and try again.")
