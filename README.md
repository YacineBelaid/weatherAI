# Weather AI

Intelligent weather assistant with chat interface.

## Quick Start

1. **Backend:**

   ```bash
   python start.py --mode backend
   ```

2. **Frontend:**

   ```bash
   cd frontend
   npm install
   npm start
   ```

3. **Test:**
   ```bash
   python test_services.py
   ```

## Architecture

```
Frontend → NLP → Ollama → Geocoding → Playwright
```

- **Frontend**: React chat interface
- **NLP**: spaCy for query parsing
- **Ollama**: Local LLM fallback
- **Playwright**: Weather.com scraping

## Services

- Main Service: `http://localhost:8000`
- NLP Service: `http://localhost:8001`
- Ollama Service: `http://localhost:8002`
- Playwright Service: `http://localhost:8008`

## Usage

Ask about weather or outdoor activities:

- "Weather in Paris"
- "Best beach today"
- "Temperature in Madrid"
