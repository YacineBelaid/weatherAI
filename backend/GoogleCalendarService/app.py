"""
Google Calendar Service for calendar integration
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import os
from datetime import datetime, timedelta
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(title="Google Calendar Service", version="1.0.0")

# Google Calendar configuration
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")


class CalendarRequest(BaseModel):
    location: str
    date: Optional[str] = None  # YYYY-MM-DD format
    time_range: Optional[Dict[str, str]] = None  # {"start": "09:00", "end": "17:00"}


class CalendarEvent(BaseModel):
    title: str
    start_time: str
    end_time: str
    location: Optional[str] = None
    description: Optional[str] = None


class CalendarResponse(BaseModel):
    location: str
    date: str
    events: List[CalendarEvent]
    availability: Dict[str, Any]
    source: str
    success: bool
    error: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    credentials_available = os.path.exists(GOOGLE_CREDENTIALS_FILE)
    token_available = os.path.exists(GOOGLE_TOKEN_FILE)
    
    return {
        "status": "healthy" if credentials_available else "unhealthy",
        "service": "google-calendar-service",
        "credentials_configured": credentials_available,
        "token_available": token_available
    }


@app.post("/calendar", response_model=CalendarResponse)
async def get_calendar_info(request: CalendarRequest):
    """
    Get calendar information for a location and date
    
    Returns events and availability information
    """
    try:
        logger.info("Getting calendar information", location=request.location, date=request.date)
        
        # Check if Google Calendar is configured
        if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
            return CalendarResponse(
                location=request.location,
                date=request.date or datetime.now().strftime("%Y-%m-%d"),
                events=[],
                availability={"available": True, "reason": "No calendar configured"},
                source="mock",
                success=True,
                error="Google Calendar not configured"
            )
        
        # For now, return mock data
        # In a real implementation, you would integrate with Google Calendar API
        mock_events = [
            CalendarEvent(
                title="Team Meeting",
                start_time="09:00",
                end_time="10:00",
                location="Conference Room A",
                description="Weekly team standup"
            ),
            CalendarEvent(
                title="Lunch",
                start_time="12:00",
                end_time="13:00",
                location="Restaurant",
                description="Lunch with client"
            )
        ]
        
        # Mock availability check
        availability = {
            "available": True,
            "free_slots": [
                {"start": "10:00", "end": "12:00"},
                {"start": "13:00", "end": "17:00"}
            ],
            "weather_considerations": {
                "outdoor_activities": "Good weather for outdoor activities",
                "indoor_activities": "Consider indoor alternatives if weather is poor"
            }
        }
        
        return CalendarResponse(
            location=request.location,
            date=request.date or datetime.now().strftime("%Y-%m-%d"),
            events=mock_events,
            availability=availability,
            source="mock",
            success=True
        )
        
    except Exception as e:
        logger.error("Error getting calendar information", location=request.location, error=str(e))
        return CalendarResponse(
            location=request.location,
            date=request.date or datetime.now().strftime("%Y-%m-%d"),
            events=[],
            availability={"available": False, "reason": "Error occurred"},
            source="error",
            success=False,
            error=str(e)
        )


@app.post("/availability")
async def check_availability(request: CalendarRequest):
    """
    Check availability for outdoor activities based on weather and calendar
    """
    try:
        logger.info("Checking availability", location=request.location, date=request.date)
        
        # Mock availability check
        # In a real implementation, you would:
        # 1. Get weather data
        # 2. Check calendar for conflicts
        # 3. Consider time of day, season, etc.
        
        availability = {
            "available": True,
            "recommended_times": ["09:00-12:00", "14:00-17:00"],
            "weather_rating": "Good",
            "considerations": [
                "Perfect weather for outdoor activities",
                "No conflicting meetings",
                "Good visibility and comfortable temperature"
            ]
        }
        
        return availability
        
    except Exception as e:
        logger.error("Error checking availability", location=request.location, error=str(e))
        return {
            "available": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
