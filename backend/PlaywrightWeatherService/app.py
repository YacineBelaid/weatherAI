from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import structlog
import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import urllib.parse

logger = structlog.get_logger()
app = FastAPI()

WEATHER_COM_BASE_URL = "https://weather.com"

class WeatherRequest(BaseModel):
    location: str
    intent: str
    time_reference: Optional[Dict[str, Any]] = None
    weather_params: list = []

class WeatherResponse(BaseModel):
    location: str
    temperature: Optional[str] = None
    condition: Optional[str] = None
    source: str = "playwright"
    success: bool = False
    error: str = ""

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest):
    try:
        location = request.location
        logger.info("Processing weather request", location=location)
        
        url = await get_weather_url(location)
        if not url:
            return WeatherResponse(
                location=location,
                source="playwright",
                success=False,
                error="Could not generate weather URL"
            )
        
        weather_data = await scrape_weather(url, location)
        if not weather_data:
            return WeatherResponse(
                location=location,
                source="playwright",
                success=False,
                error="Failed to scrape weather data"
            )
        
        return weather_data
        
    except Exception as e:
        logger.error("Error processing weather request", location=request.location, error=str(e))
        return WeatherResponse(
            location=request.location,
            source="playwright",
            success=False,
            error=f"Error processing request: {str(e)}"
        )

async def get_weather_url(location: str) -> Optional[str]:
    try:
        import urllib.parse
        
        coordinates = await get_coordinates(location)
        if coordinates:
            lat, lon = coordinates
            url = f"{WEATHER_COM_BASE_URL}/weather/today/l/{lat},{lon}"
            logger.info("Using coordinates URL", url=url, lat=lat, lon=lon)
            return url
        
        encoded_location = urllib.parse.quote(location)
        url_patterns = [
            f"{WEATHER_COM_BASE_URL}/search?q={encoded_location}",
            f"{WEATHER_COM_BASE_URL}/weather/today/l/{encoded_location}",
            f"{WEATHER_COM_BASE_URL}/fr-FR/temps/aujour/l/{encoded_location}",
        ]
        
        async with httpx.AsyncClient(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
            },
            timeout=15.0,
            follow_redirects=True
        ) as client:
            
            for url in url_patterns:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        logger.info("Found working URL", url=url)
                        return url
                except Exception as e:
                    logger.warning("URL test failed", url=url, error=str(e))
                    continue
            
            return f"{WEATHER_COM_BASE_URL}/"
            
    except Exception as e:
        logger.error("Error getting weather URL", location=location, error=str(e))
        return None

async def get_coordinates(location: str) -> Optional[tuple]:
    try:
        import urllib.parse
        
        encoded_location = urllib.parse.quote(location)
        geocoding_url = f"https://nominatim.openstreetmap.org/search?q={encoded_location}&format=json&limit=1"
        
        async with httpx.AsyncClient(
            headers={'User-Agent': 'WeatherAI/1.0'},
            timeout=10.0
        ) as client:
            response = await client.get(geocoding_url)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    logger.info("Got coordinates", location=location, lat=lat, lon=lon)
                    return (lat, lon)
        
        return None
    except Exception as e:
        logger.error("Error getting coordinates", location=location, error=str(e))
        return None

async def scrape_weather(url: str, location: str) -> Optional[WeatherResponse]:
    try:
        from playwright.async_api import async_playwright
        from bs4 import BeautifulSoup
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',
                    '--disable-javascript',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-translate',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--no-first-run',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ]
            )
            
            try:
                logger.info("Launching browser", url=url)
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Cache-Control': 'max-age=0',
                        'DNT': '1',
                    }
                )
                
                page = await context.new_page()
                
                logger.info("Navigating to page", url=url)
                response = await page.goto(url, wait_until='networkidle', timeout=30000)
                
                logger.info("Actual URL visited", url=page.url)
                
                if response and response.status == 404:
                    logger.error("404", url=url)
                    return WeatherResponse(
                        location=location,
                        source="playwright",
                        success=False,
                        error=f"404 - Page not found: {url}"
                    )
                
                try:
                    await page.wait_for_selector('body', timeout=10000)
                except:
                    logger.warning("Page load timeout, continuing anyway")
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                title = soup.find('title')
                logger.info("Page title", title=title.get_text() if title else "No title")
                
                temp_elements = soup.select('span[data-testid="TemperatureValue"]')
                logger.info("Found temperature elements", count=len(temp_elements))
                
                temperature = extract_temperature(soup)
                condition = extract_condition(soup)
                
                if not temperature and not condition:
                    logger.warning("No weather data extracted", url=url, location=location)
                    return WeatherResponse(
                        location=location,
                        source="playwright",
                        success=False,
                        error="No weather data found on page"
                    )
                
                weather_data = {
                    "location": location,
                    "source": "playwright",
                    "success": True
                }
                
                if temperature and temperature != "N/A":
                    weather_data["temperature"] = temperature
                if condition and condition != "N/A" and condition != "Unknown":
                    weather_data["condition"] = condition
                
                return WeatherResponse(**weather_data)
                
            finally:
                await browser.close()
                
    except Exception as e:
        logger.error("Error scraping weather", location=location, error=str(e))
        return WeatherResponse(
            location=location,
            source="playwright",
            success=False,
            error=f"Error scraping weather data: {str(e)}"
        )

def extract_temperature(soup) -> str:
    try:
        from bs4 import BeautifulSoup
        
        temp_element = soup.select_one('span[data-testid="TemperatureValue"].CurrentConditions--tempValue--zUBSz')
        if temp_element:
            temp_text = temp_element.get_text().strip()
            temp_match = re.search(r'(\d+)', temp_text)
            if temp_match:
                return f"{temp_match.group(1)}°C"
        
        temp_elements = soup.select('span[data-testid="TemperatureValue"]')
        for element in temp_elements:
            if element.find_parent(class_=re.compile(r'CurrentConditions')):
                temp_text = element.get_text().strip()
                temp_match = re.search(r'(\d+)', temp_text)
                if temp_match:
                    return f"{temp_match.group(1)}°C"
        
        return None
    except Exception:
        return None

def extract_condition(soup) -> str:
    try:
        from bs4 import BeautifulSoup
        
        condition_element = soup.select_one('div[data-testid="wxPhrase"].CurrentConditions--phraseValue---VS-k')
        if condition_element:
            condition_text = condition_element.get_text().strip()
            if condition_text:
                return condition_text
        
        condition_elements = soup.select('div[data-testid="wxPhrase"]')
        for element in condition_elements:
            if element.find_parent(class_=re.compile(r'CurrentConditions')):
                condition_text = element.get_text().strip()
                if condition_text:
                    return condition_text
        
        return None
    except Exception:
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)