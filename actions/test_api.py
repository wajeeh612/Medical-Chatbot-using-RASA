import requests


# Test if Ollama API is accessible
try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma3:4b",
            "prompt": "Hello, are you working?",
            "stream": False
        },
        timeout=180
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ Ollama is running and connected!")
        print(f"Model response: {result['response']}")
    else:
        print(f"❌ Error: Status code {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ Ollama is not running!")
    print("Start it with: ollama serve")

except Exception as e:
    print(f"❌ Error: {e}")