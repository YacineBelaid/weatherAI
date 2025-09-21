import requests

def test_services():
    services = [
        ("Main Service", "http://localhost:8000/health"),
        ("NLP Service", "http://localhost:8001/health"),
        ("Ollama Service", "http://localhost:8002/health"),
        ("Playwright Service", "http://localhost:8008/health")
    ]
    
    print("🔍 Testing services...")
    all_healthy = True
    
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Healthy")
            else:
                print(f"❌ {name}: Unhealthy")
                all_healthy = False
        except:
            print(f"❌ {name}: Error")
            all_healthy = False
    
    if not all_healthy:
        print("\n⚠️ Some services are not healthy. Please start all services first.")
        return False
    
    print("\n✅ All services are healthy!")
    return True

def test_weather_query(query: str, location: str = None):
    try:
        payload = {"query": query}
        if location:
            payload["user_location"] = location
        
        response = requests.post("http://localhost:8000/ask", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n🌤️ Query: {query}")
            print(f"🤖 Response: {result.get('response', 'No response')}")
            
            if result.get('weather_data'):
                weather = result['weather_data']
                print(f"🌡️ Temperature: {weather.get('temperature', 'N/A')}")
                print(f"☁️ Condition: {weather.get('condition', 'N/A')}")
            
            return result
        else:
            print(f"❌ Weather query failed: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Weather query error: {str(e)}")
        return {}

def main():
    print("🚀 Weather AI Services Test")
    print("=" * 50)
    
    if not test_services():
        return
    
    test_queries = [
        ("Weather in Paris", None),
        ("Temperature in Madrid", None),
        ("Best beach today", "Miami")
    ]
    
    for query, location in test_queries:
        test_weather_query(query, location)
        print("-" * 50)

if __name__ == "__main__":
    main()