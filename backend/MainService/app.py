from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import structlog
import json
import os

logger = structlog.get_logger()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WeatherQuery(BaseModel):
    query: str
    user_location: Optional[str] = None
    chat_history: Optional[List[Dict[str, str]]] = None

class WeatherResponse(BaseModel):
    response: str
    status: str
    parsed_query: Dict[str, Any]
    weather_data: Optional[Dict[str, Any]] = None
    processing_method: str
    requires_location: bool = False
    suggested_actions: Optional[List[str]] = None

KEYWORDS_FILE = "dynamic_keywords.json"

def load_dynamic_keywords() -> Dict[str, List[str]]:
    try:
        if os.path.exists(KEYWORDS_FILE):
            with open(KEYWORDS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        "situational": ["where", "best place", "worst place", "should go", "can go"],
        "weather": ["weather", "temperature", "forecast", "rain", "sunny"]
    }

def save_dynamic_keywords(keywords: Dict[str, List[str]]):
    try:
        with open(KEYWORDS_FILE, 'w') as f:
            json.dump(keywords, f, indent=2)
    except:
        pass

def update_keywords_from_ollama(query: str, ollama_result: Dict[str, Any]):
    keywords = load_dynamic_keywords()
    query_lower = query.lower()
    new_keywords = []
    
    words = query_lower.split()
    for word in words:
        if len(word) > 3 and word not in keywords["situational"] and word not in keywords["weather"]:
            if any(phrase in query_lower for phrase in ["where", "best", "worst", "should", "can"]):
                new_keywords.append(word)
    
    if new_keywords:
        keywords["situational"].extend(new_keywords)
        keywords["situational"] = list(set(keywords["situational"]))
        save_dynamic_keywords(keywords)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/ask", response_model=WeatherResponse)
async def ask_weather(query: WeatherQuery):
    try:
        # Check for recommendation patterns FIRST, before calling NLP
        query_lower = query.query.lower()
        parsed_query = None
        
        if any(keyword in query_lower for keyword in ["best", "top", "recommend", "suggest"]) and "in" in query_lower:
            if any(keyword in query_lower for keyword in ["mountain", "mountains", "peak", "peaks", "summit", "summits"]):
                parsed_query = {
                    "original_query": query.query,
                    "intent": "mountain_recommendation",
                    "location": "Nepal" if "nepal" in query_lower else None,
                    "confidence": 0.9,
                    "processing_method": "fallback"
                }
            elif any(keyword in query_lower for keyword in ["beach", "beaches", "coast", "shore", "seaside"]):
                # Extract country from "in [country]" pattern
                import re
                in_pattern = r'\bin\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)'
                match = re.search(in_pattern, query.query)
                country = match.group(1).title() if match else None
                
                parsed_query = {
                    "original_query": query.query,
                    "intent": "beach_recommendation",
                    "location": country,
                    "confidence": 0.9,
                    "processing_method": "fallback"
                }
            elif any(keyword in query_lower for keyword in ["city", "cities", "town", "urban"]):
                # Extract country from "in [country]" pattern
                import re
                in_pattern = r'\bin\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)'
                match = re.search(in_pattern, query.query)
                country = match.group(1).title() if match else None
                
                parsed_query = {
                    "original_query": query.query,
                    "intent": "city_recommendation",
                    "location": country,
                    "confidence": 0.9,
                    "processing_method": "fallback"
                }
        
        # If no recommendation detected, try NLP
        if not parsed_query:
            parsed_query = await try_nlp(query.query)
        
        # Always try Ollama for keyword enrichment and better parsing
        ollama_result = await try_ollama(query.query)
        if ollama_result:
            update_keywords_from_ollama(query.query, ollama_result)
            # Use Ollama result if it has higher confidence or better intent detection
            if not parsed_query or ollama_result.get("confidence", 0) > parsed_query.get("confidence", 0):
                parsed_query = ollama_result
        
        # Handle recommendation queries first
        if parsed_query and parsed_query.get("intent") in ["recommendation", "beach_recommendation", "city_recommendation", "mountain_recommendation"]:
            return await handle_recommendation_query(parsed_query)
        
        if parsed_query and parsed_query.get("intent") == "situational":
            if not query.user_location:
                return handle_situational_query(query.query)
            else:
                location = query.user_location
                parsed_query = {
                    "original_query": query.query,
                    "intent": "weather",
                    "location": location,
                    "confidence": 0.9,
                    "processing_method": "user_location"
                }
        
        # Handle recommendation queries first
        if parsed_query and parsed_query.get("intent") in ["recommendation", "beach_recommendation", "city_recommendation", "mountain_recommendation"]:
            return await handle_recommendation_query(parsed_query)
        
        if parsed_query and parsed_query.get("intent") == "situational":
            if not query.user_location:
                return handle_situational_query(query.query)
            else:
                location = query.user_location
                parsed_query = {
                    "original_query": query.query,
                    "intent": "weather",
                    "location": location,
                    "confidence": 0.9,
                    "processing_method": "user_location"
                }
        
        location = query.user_location or (parsed_query.get("location") if parsed_query else None)
        
        if not location:
            return WeatherResponse(
                response="I need a location to provide weather information. Please specify a city or place.",
                status="error",
                parsed_query={"original_query": query.query, "error": "No location found"},
                processing_method="none",
                requires_location=True,
                suggested_actions=["Please provide your city or location"]
            )
        
        weather_data = await try_playwright(parsed_query)
        
        if weather_data and weather_data.get("success"):
            response_text = format_response(weather_data, parsed_query)
            status = "success"
        else:
            response_text = f"Sorry, I couldn't get weather data for {location}"
            status = "error"
        
        return WeatherResponse(
            response=response_text,
            status=status,
            parsed_query=parsed_query,
            weather_data=weather_data,
            processing_method=parsed_query.get("processing_method", "unknown")
        )
        
    except Exception as e:
        return WeatherResponse(
            response=f"Sorry, I encountered an error: {str(e)}",
            status="error",
            parsed_query={"original_query": query.query, "error": str(e)},
            processing_method="error"
        )

def handle_situational_query(query: str) -> WeatherResponse:
    query_lower = query.lower()
    
    # Provide more logical suggestions based on the query type
    if any(keyword in query_lower for keyword in ["mountain", "mountains", "peak", "peaks", "summit"]):
        suggestions = [
            "Tell me your location to find nearby mountains",
            "Or ask about specific mountains (e.g., 'Weather at Everest Base Camp')",
            "Or ask about mountains in a country (e.g., 'Mountains in Nepal weather')"
        ]
    elif any(keyword in query_lower for keyword in ["beach", "beaches", "coast", "shore"]):
        suggestions = [
            "Tell me your location to find nearby beaches", 
            "Or ask about specific beaches (e.g., 'Weather at Miami Beach')",
            "Or ask about beaches in a country (e.g., 'Beaches in Spain weather')"
        ]
    elif any(keyword in query_lower for keyword in ["city", "cities", "town"]):
        suggestions = [
            "Tell me your location to find nearby cities",
            "Or ask about specific cities (e.g., 'Weather in Paris')",
            "Or ask about cities in a country (e.g., 'Cities in Italy weather')"
        ]
    else:
        suggestions = [
            "Tell me your current location",
            "Or ask about a specific place (e.g., 'Weather in Paris')",
            "Or ask about places in a region (e.g., 'Best places in Europe')"
        ]
    
    return WeatherResponse(
        response="I would love to help you find that place! To give you accurate weather information, could you tell me your current city or location?",
        status="location_required",
        parsed_query={"original_query": query, "intent": "situational_recommendation"},
        processing_method="situational",
        requires_location=True,
        suggested_actions=suggestions
    )

async def handle_recommendation_query(parsed_query: Dict[str, Any]) -> WeatherResponse:
    intent = parsed_query.get("intent", "recommendation")
    location = parsed_query.get("location", "Unknown")
    original_query = parsed_query.get("original_query", "").lower()
    
    # If location is empty but we can detect it from the query, extract it
    if not location or location == "Unknown":
        if "nepal" in original_query:
            location = "Nepal"
        elif "switzerland" in original_query:
            location = "Switzerland"
        elif "france" in original_query:
            location = "France"
        elif "italy" in original_query:
            location = "Italy"
        elif "spain" in original_query:
            location = "Spain"
    
    recommendation_type = "beach" if "beach" in intent else "city" if "city" in intent else "mountain" if "mountain" in intent else "place"
    
    query_text = f"Famous mountains in {location}" if recommendation_type == "mountain" else f"Best {recommendation_type}s in {location}"
    recommendations = await get_recommendations_from_ollama(query_text)
    locations = recommendations.get("locations", [])
    
    if recommendation_type == "mountain":
        mountain_fallback = {
            "Switzerland": ["Matterhorn", "Jungfrau", "Eiger", "Pilatus", "Rigi"],
            "switzerland": ["Matterhorn", "Jungfrau", "Eiger", "Pilatus", "Rigi"],
            "France": ["Mont Blanc", "Mont Ventoux", "Pic du Midi", "Chamonix", "Annecy"],
            "france": ["Mont Blanc", "Mont Ventoux", "Pic du Midi", "Chamonix", "Annecy"],
            "Italy": ["Matterhorn", "Monte Bianco", "Dolomites", "Gran Paradiso", "Monte Rosa"],
            "italy": ["Matterhorn", "Monte Bianco", "Dolomites", "Gran Paradiso", "Monte Rosa"],
            "Spain": ["Teide", "Mulhacén", "Aneto", "Pico de Europa", "Nevado"],
            "spain": ["Teide", "Mulhacén", "Aneto", "Pico de Europa", "Nevado"],
            "Austria": ["Grossglockner", "Zugspitze", "Kitzbühel", "Innsbruck", "Salzburg"],
            "austria": ["Grossglockner", "Zugspitze", "Kitzbühel", "Innsbruck", "Salzburg"],
            "Nepal": ["Mount Everest", "K2", "Makalu", "Cho Oyu", "Lhotse"],
            "nepal": ["Mount Everest", "K2", "Makalu", "Cho Oyu", "Lhotse"]
        }
        if location in mountain_fallback:
            locations = mountain_fallback[location]
        elif not location or location == "Unknown":
            # If no specific location, try to detect from the original query
            original_query = parsed_query.get("original_query", "").lower()
            if "nepal" in original_query:
                locations = ["Mount Everest", "K2", "Makalu", "Cho Oyu", "Lhotse"]
                location = "Nepal"  # Set the location for display
    
    if not locations:
        return WeatherResponse(
            response=f"Sorry, I couldn't find recommendations for {recommendation_type}s in {location}.",
            status="error",
            parsed_query=parsed_query,
            processing_method="ollama"
        )
    
    weather_results = []
    for loc in locations[:3]:
        weather_data = await try_playwright({
            "original_query": f"Weather in {loc}",
            "intent": "weather",
            "location": loc,
            "confidence": 0.9,
            "processing_method": "recommendation"
        })
        
        if weather_data and weather_data.get("success"):
            weather_results.append({
                "location": loc,
                "temperature": weather_data.get("temperature", "N/A"),
                "condition": weather_data.get("condition", "N/A")
            })
    
    if not weather_results:
        return WeatherResponse(
            response=f"Sorry, I couldn't get weather data for the recommended {recommendation_type}s in {location}.",
            status="error",
            parsed_query=parsed_query,
            processing_method="playwright"
        )
    
    response_parts = [f"Best {recommendation_type}s in {location} today:"]
    for result in weather_results:
        response_parts.append(f"🏙️ {result['location']}: {result['temperature']}, {result['condition']}")
    
    return WeatherResponse(
        response=" ".join(response_parts),
        status="success",
        parsed_query=parsed_query,
        processing_method="recommendation"
    )

async def get_recommendations_from_ollama(query: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("http://localhost:8002/recommend", json={"query": query})
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return {"locations": []}

async def try_nlp(query: str) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post("http://localhost:8001/parse", json={"query": query})
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return None

async def try_ollama(query: str) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("http://localhost:8002/parse", json={"query": query})
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return None

async def try_playwright(parsed_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post("http://localhost:8008/weather", json=parsed_query)
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return None

def format_response(weather_data: Dict[str, Any], parsed_query: Dict[str, Any]) -> str:
    location = weather_data.get("location", "Unknown")
    response_parts = [f"Here's the weather for {location}:"]
    
    if weather_data.get("temperature") and weather_data["temperature"] != "N/A":
        response_parts.append(f"🌡️ Temperature: {weather_data['temperature']}")
    
    if weather_data.get("condition") and weather_data["condition"] != "N/A" and weather_data["condition"] != "Unknown":
        response_parts.append(f"☁️ Condition: {weather_data['condition']}")
    
    return " ".join(response_parts)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)