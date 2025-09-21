from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import spacy
import structlog
import json
import os
import re

# INTERFACES
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    original_query: str
    intent: str
    location: Optional[str] = None
    confidence: float
    processing_method: str


logger = structlog.get_logger()
app = FastAPI()

def load_dynamic_keywords() -> Dict[str, List[str]]:
    try:
        if os.path.exists("dynamic_keywords.json"):
            with open("dynamic_keywords.json", 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        "situational": ["where", "should go", "can go", "where to", "recommend me"],
        "weather": ["weather", "temperature", "forecast", "rain", "sunny"],
        "recommendation": ["best", "top", "recommend", "suggest", "favorite", "popular"],
        "location": ["beach", "coast", "shore", "seaside", "ocean", "sea", "coastal", "mountain", "peak", "summit", "hill", "alpine", "hiking", "climbing", "city", "town", "urban", "metropolitan", "downtown", "capital", "village", "resort", "park", "forest", "lake", "river", "island", "peninsula", "valley", "desert", "canyon", "volcano", "glacier", "waterfall", "cave", "monument", "landmark", "attraction", "destination"]
    }

def save_dynamic_keywords(keywords: Dict[str, List[str]]):
    try:
        with open("dynamic_keywords.json", 'w') as f:
            json.dump(keywords, f)
    except:
        pass

async def enrich_keywords_with_ollama():
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("http://localhost:8002/enrich_keywords", json={})
            if response.status_code == 200:
                enriched = response.json()
                current = load_dynamic_keywords()
                for category, keywords in enriched.items():
                    if category in current:
                        current[category].extend(keywords)
                        current[category] = list(set(current[category]))
                save_dynamic_keywords(current)
    except:
        pass

try:
    nlp = spacy.load("en_core_web_sm")
    model_loaded = True
    logger.info("spaCy model loaded successfully")
except Exception as e:
    nlp = None
    model_loaded = False
    logger.error("Failed to load spaCy model", error=str(e))

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "service": "nlp-service",
        "model_loaded": model_loaded
    }

@app.post("/parse", response_model=QueryResponse)
async def parse_query(request: QueryRequest):
    if not model_loaded:
        raise HTTPException(status_code=500, detail="NLP model not loaded")
    
    try:
        result = parse_query_text(request.query)
        return QueryResponse(**result)
    except Exception as e:
        logger.error("Error parsing query", query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error parsing query: {str(e)}")

def parse_query_text(query: str) -> Dict[str, Any]:
    doc = nlp(query)
    location = None
    intent = "general_weather"
    confidence = 0.5
    query_lower = query.lower()
    
    dynamic_keywords = load_dynamic_keywords()
    
    # Check for recommendation patterns FIRST: "best [type] in [country]"
    if any(keyword in query_lower for keyword in dynamic_keywords.get("recommendation", [])) and "in" in query_lower:
        recommendation_type = None
        location_keywords = dynamic_keywords.get("location", [])
        
        # Detect specific location types based on keywords
        if any(keyword in query_lower for keyword in ["beach", "coast", "shore", "seaside", "ocean", "sea", "coastal", "beaches"]):
            recommendation_type = "beach"
        elif any(keyword in query_lower for keyword in ["mountain", "peak", "summit", "hill", "alpine", "hiking", "climbing", "mountains", "peaks", "summits"]):
            recommendation_type = "mountain"
        elif any(keyword in query_lower for keyword in ["city", "town", "urban", "metropolitan", "downtown", "capital", "cities"]):
            recommendation_type = "city"
        elif any(keyword in query_lower for keyword in location_keywords):
            recommendation_type = "place"
        elif "place" in query_lower or "places" in query_lower:
            recommendation_type = "place"
        
        in_pattern = r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        match = re.search(in_pattern, query)
        if match and recommendation_type:
            return {
                "original_query": query,
                "intent": "recommendation",
                "location": None,
                "confidence": 0.9,
                "processing_method": "spacy",
                "recommendation_type": recommendation_type,
                "country": match.group(1)
            }
    
    situational_keywords = dynamic_keywords.get("situational", ["where", "should go", "can go"])
    if any(keyword in query_lower for keyword in situational_keywords) and not any(keyword in query_lower for keyword in dynamic_keywords.get("recommendation", [])):
        return {
            "original_query": query,
            "intent": "situational",
            "location": None,
            "confidence": 0.9,
            "processing_method": "spacy"
        }
    
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            location = ent.text
            confidence = 0.8
            break
    
    if not location:
        skip_words = ["weather", "temperature", "forecast", "today", "tomorrow", "yesterday"]
        for token in doc:
            if token.pos_ == "PROPN" and token.is_alpha and len(token.text) > 2 and token.text.lower() not in skip_words:
                location = token.text
                confidence = 0.6
                break
    
    if not location:
        in_pattern = r'\bin\s+([A-Z][a-z]+)'
        match = re.search(in_pattern, query)
        if match:
            location = match.group(1)
            confidence = 0.7
    
    weather_keywords = {
        "temperature": ["temperature", "temp", "hot", "cold", "warm", "cool"],
        "current_weather": ["weather", "forecast", "conditions"],
        "humidity": ["humidity", "humid", "moisture"],
        "wind": ["wind", "breeze", "gusty"],
        "precipitation": ["rain", "snow", "precipitation", "storm", "drizzle"]
    }
    
    for intent_type, keywords in weather_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            intent = intent_type
            confidence = min(confidence + 0.2, 0.9)
            break
    
    return {
        "original_query": query,
        "intent": intent,
        "location": location,
        "confidence": confidence,
        "processing_method": "spacy"
    }

@app.post("/parse", response_model=QueryResponse)
async def parse_query(request: QueryRequest):
    try:
        await enrich_keywords_with_ollama()
        result = parse_query_text(request.query)
        return QueryResponse(**result)
    except Exception as e:
        logger.error("Error parsing query", query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error parsing query: {str(e)}")

@app.post("/update_keywords")
async def update_keywords(keywords: Dict[str, List[str]]):
    try:
        current = load_dynamic_keywords()
        for category, new_keywords in keywords.items():
            if category in current:
                current[category].extend(new_keywords)
                current[category] = list(set(current[category]))
            else:
                current[category] = new_keywords
        save_dynamic_keywords(current)
        return {"status": "updated", "keywords": current}
    except Exception as e:
        logger.error("Error updating keywords", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error updating keywords: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)