#!/usr/bin/env python3
"""
Test script for Google Calendar Service
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

async def test_google_calendar():
    """Test Google Calendar service endpoints"""
    
    base_url = "http://localhost:8005"
    
    print("Testing Google Calendar Service...")
    print("=" * 50)
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test list calendars
    print("\n2. Testing list calendars...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/calendars")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                calendars = response.json()
                print(f"Found {len(calendars)} calendars")
                for cal in calendars[:3]:
                    print(f"- {cal.get('summary', 'No Title')} ({cal.get('id', 'No ID')})")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test list events from primary calendar
    print("\n3. Testing list events...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/calendars/primary/events")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                events = response.json()
                print(f"Found {len(events)} events")
                for event in events[:3]:
                    start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'No time'))
                    print(f"- {event.get('summary', 'No Title')} at {start}")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test freebusy
    print("\n4. Testing freebusy...")
    try:
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        
        freebusy_request = {
            "timeMin": now.isoformat() + 'Z',
            "timeMax": tomorrow.isoformat() + 'Z',
            "items": [{"id": "primary"}]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{base_url}/freebusy", json=freebusy_request)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                freebusy = response.json()
                print(f"Freebusy data: {freebusy}")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test settings
    print("\n5. Testing settings...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/settings")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                settings = response.json()
                print(f"Found {len(settings)} settings")
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Google Calendar Service Test")
    print("Make sure the service is running on port 8005")
    print("=" * 50)
    
    asyncio.run(test_google_calendar())
    
    print("\nTest completed!")
