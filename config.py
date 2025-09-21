"""
Weather AI Agent Configuration
"""

# Service URLs
SERVICES = {
    "main": "http://localhost:8000",
    "nlp": "http://localhost:8001",
    "weather_scraper": "http://localhost:8004",
    "puppeteer": "http://localhost:8006",
    "calendar": "http://localhost:8005"
}

# Frontend
FRONTEND_URL = "http://localhost:3000"

# API Keys (optional)
API_KEYS = {
    "IBM_WEATHER_API_KEY": None,
    "WEATHER_COM_API_KEY": None
}

# Test Configuration
TEST_TIMEOUT = 30
TEST_RETRIES = 3
