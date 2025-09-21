from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import spacy
import structlog
import json
import os
import re

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
        "situational": ["where", "best place", "worst place", "should go", "can go"],
        "weather": ["weather", "temperature", "forecast", "rain", "sunny"]
    }

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    original_query: str
    intent: str
    location: Optional[str] = None
    confidence: float
    processing_method: str

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
    
    if "best" in query_lower and "in" in query_lower:
        recommendation_type = None
        if "city" in query_lower or "cities" in query_lower:
            recommendation_type = "city"
        elif "beach" in query_lower or "beaches" in query_lower:
            recommendation_type = "beach"
        elif "mountain" in query_lower or "mountains" in query_lower:
            recommendation_type = "mountain"
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
    
    dynamic_keywords = load_dynamic_keywords()
    situational_keywords = dynamic_keywords.get("situational", ["where", "best place"])
    if any(keyword in query_lower for keyword in situational_keywords) and not ("best" in query_lower and "in" in query_lower):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)