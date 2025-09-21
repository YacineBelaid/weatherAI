from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import structlog
import json

logger = structlog.get_logger()
app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    original_query: str
    intent: str
    location: Optional[str] = None
    confidence: float
    processing_method: str

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:latest"

@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            ollama_available = response.status_code == 200
    except:
        ollama_available = False
    
    return {
        "status": "healthy", 
        "service": "ollama-service",
        "ollama_available": ollama_available
    }

@app.post("/parse", response_model=QueryResponse)
async def parse_query(request: QueryRequest):
    try:
        result = await parse_with_ollama(request.query)
        return QueryResponse(**result)
    except Exception as e:
        logger.error("Error parsing query with Ollama", query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error parsing query: {str(e)}")

@app.post("/recommend")
async def get_recommendations(request: QueryRequest):
    try:
        result = await get_recommendations_with_ollama(request.query)
        return result
    except Exception as e:
        logger.error("Error getting recommendations with Ollama", query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@app.post("/enrich_keywords")
async def enrich_keywords():
    try:
        system_prompt = '''You are a keyword enrichment assistant. Generate comprehensive lists of synonyms and related terms for different categories.

Return ONLY a valid JSON response with this structure:
{
    "recommendation": ["best", "top", "recommend", "suggest", "favorite", "popular", "excellent", "outstanding", "premium", "quality"],
    "location": ["beach", "coast", "shore", "seaside", "ocean", "sea", "coastal", "seashore", "waterfront", "lakeside", "bay", "cove", "mountain", "peak", "summit", "hill", "alpine", "hiking", "climbing", "ridge", "range", "highland", "elevation", "majestic", "city", "town", "urban", "metropolitan", "downtown", "capital", "municipality", "settlement", "borough", "village", "resort", "park", "forest", "lake", "river", "island", "peninsula", "valley", "desert", "canyon", "volcano", "glacier", "waterfall", "cave", "monument", "landmark", "attraction", "destination"],
    "situational": ["where", "best place", "worst place", "should go", "can go", "where to", "recommend me", "suggest me", "advise me"]
}

Generate 10-15 synonyms for each category. Focus on common, natural language terms people use in travel and weather queries.'''
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": system_prompt,
            "stream": False,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "{}")
                try:
                    return json.loads(response_text)
                except:
                    return {}
            else:
                return {}
    except:
        return {}

async def get_recommendations_with_ollama(query: str) -> Dict[str, Any]:
    system_prompt = '''You are a travel and location recommendation assistant. Given a query about finding places in a country, return a JSON list of specific locations.

EXAMPLES:
Query: "Best cities in Spain" → {"locations": ["Madrid", "Barcelona", "Seville", "Valencia", "Bilbao"]}
Query: "Best beaches in Italy" → {"locations": ["Sardinia", "Sicily", "Amalfi Coast", "Cinque Terre", "Rimini"]}
Query: "Best mountains in France" → {"locations": ["Mont Blanc", "Chamonix", "Annecy", "Grenoble", "Nice"]}
Query: "Best mountains in Switzerland" → {"locations": ["Matterhorn", "Jungfrau", "Eiger", "Mont Blanc", "Pilatus"]}

JSON STRUCTURE:
{
    "locations": ["list", "of", "specific", "mountains", "cities", "or", "regions"]
}

RULES:
- For MOUNTAINS: Return actual mountain names (e.g., "Matterhorn", "Mont Blanc", "Eiger"), NOT cities
- For CITIES: Return city names (e.g., "Madrid", "Barcelona", "Paris")
- For BEACHES: Return beach/coastal area names (e.g., "Sardinia", "Costa Brava")
- IMPORTANT: If asking for mountains, return mountain names, not cities near mountains
- Return 3-5 specific locations, not countries
- Focus on well-known destinations
- Return ONLY valid JSON, no other text'''

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{system_prompt}\n\nQuery: {query}",
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "{}")
            try:
                return json.loads(response_text)
            except:
                return {"locations": []}
        else:
            return {"locations": []}

async def send_keywords_to_nlp(keywords: Dict[str, List[str]]):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post("http://localhost:8001/update_keywords", json=keywords)
    except:
        pass

async def parse_with_ollama(query: str) -> Dict[str, Any]:
    system_prompt = '''You are a weather query parser. Extract information from weather-related queries and return ONLY a valid JSON response.

EXAMPLES:
Query: "Temperature in Madrid" → {"intent": "temperature", "location": "Madrid", "confidence": 0.9, "keywords": {"weather": ["temperature"]}}
Query: "Weather in Paris" → {"intent": "current_weather", "location": "Paris", "confidence": 0.9, "keywords": {"weather": ["weather"]}}
Query: "Marseille" → {"intent": "general_weather", "location": "Marseille", "confidence": 0.8, "keywords": {}}
Query: "Where should I go to the beach?" → {"intent": "beach_recommendation", "location": null, "confidence": 0.9, "keywords": {"situational": ["where"], "location": ["beach"]}}
Query: "Best beaches in Miami" → {"intent": "beach_recommendation", "location": "Miami", "confidence": 0.9, "keywords": {"recommendation": ["best"], "location": ["beaches"]}}
Query: "Top peaks in Switzerland" → {"intent": "mountain_recommendation", "location": "Switzerland", "confidence": 0.9, "keywords": {"recommendation": ["top"], "location": ["peaks"]}}
Query: "Best resorts in Spain" → {"intent": "place_recommendation", "location": "Spain", "confidence": 0.9, "keywords": {"recommendation": ["best"], "location": ["resorts"]}}

JSON STRUCTURE:
{
    "intent": "current_weather|forecast|temperature|condition|humidity|wind|precipitation|general_weather|beach_recommendation|city_recommendation|mountain_recommendation",
    "location": "city name or country",
    "confidence": 0.0-1.0,
    "keywords": {
        "recommendation": ["best", "top", "excellent", "outstanding"],
        "location": ["beach", "coast", "shore", "seaside", "mountain", "peak", "summit", "hill", "city", "town", "urban", "resort", "park", "forest", "lake", "river", "island", "valley", "desert", "canyon", "volcano", "glacier", "waterfall", "cave", "monument", "landmark", "attraction", "destination"],
        "situational": ["where", "should", "can", "recommend"]
    }
}

RULES:
- Extract city names (including nicknames like "Big Apple" → "New York")
- If query is just a city name, use "general_weather" intent
- For beach/outdoor activity queries without location, use "beach_recommendation" intent
- For "best [type] in [country]" queries, use appropriate recommendation intent
- ALWAYS extract relevant keywords from the query and categorize them
- Return ONLY the JSON, no explanations
- Use confidence 0.8-0.9 for clear queries, 0.6-0.7 for ambiguous ones'''

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{system_prompt}\n\nQuery: {query}",
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": 200
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        response_text = result.get("response", "").strip()
        
        try:
            parsed = json.loads(response_text)
            parsed["original_query"] = query
            parsed["processing_method"] = "ollama"
            
            # Send keywords to NLP service for enrichment
            if "keywords" in parsed and parsed["keywords"]:
                await send_keywords_to_nlp(parsed["keywords"])
            
            return parsed
        except json.JSONDecodeError:
            logger.warning("Failed to parse Ollama response as JSON", response=response_text)
            return {
                "original_query": query,
                "intent": "general_weather",
                "location": None,
                "confidence": 0.3,
                "processing_method": "ollama"
            }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)