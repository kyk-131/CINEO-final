#!/usr/bin/env python3
"""
Cineo AI - API Key Validation Script
Test your API keys to make sure they're working correctly.
"""

import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

def test_openrouter_api():
    """Test OpenRouter API key"""
    print("🔍 Testing OpenRouter API...")

    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        return False

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Cineo AI Test"
            },
            data=json.dumps({
                "model": "x-ai/grok-4-fast:free",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50
            }),
            timeout=10
        )

        if response.status_code == 200:
            print("✅ OpenRouter API key is valid")
            return True
        else:
            print(f"❌ OpenRouter API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ OpenRouter API connection failed: {e}")
        return False

def test_stability_api():
    """Test Stability AI API key"""
    print("🔍 Testing Stability AI API...")

    api_key = os.getenv('STABILITY_API_KEY')
    if not api_key:
        print("❌ STABILITY_API_KEY not found in environment")
        return False

    try:
        response = requests.post(
            "https://api.stability.ai/v1/engines/list",
            headers={
                "Authorization": f"Bearer {api_key}"
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Stability AI API key is valid")
            return True
        else:
            print(f"❌ Stability AI API error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Stability AI API connection failed: {e}")
        return False

def test_elevenlabs_api():
    """Test ElevenLabs API key"""
    print("🔍 Testing ElevenLabs API...")

    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment")
        return False

    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={
                "xi-api-key": api_key
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ ElevenLabs API key is valid")
            return True
        else:
            print(f"❌ ElevenLabs API error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ ElevenLabs API connection failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")

    try:
        import psycopg2
        conn = psycopg2.connect(os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/cineo_db'))
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    print("🔍 Testing Redis connection...")

    try:
        import redis
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def main():
    """Run all API key tests"""
    print("🔑 Cineo AI - API Key Validation")
    print("=" * 40)
    print("Testing your API keys and connections...")
    print()

    # Load environment variables
    env_file = Path('.env')
    if env_file.exists():
        print("✅ Found .env file")
        # Load environment variables from .env file
        load_dotenv(env_file)
        print("✅ Environment variables loaded")
    else:
        print("❌ .env file not found. Run setup_api_keys.py first.")
        return

    # Test all services
    tests = [
        ("Database", test_database_connection),
        ("Redis", test_redis_connection),
        ("OpenRouter", test_openrouter_api),
        ("Stability AI", test_stability_api),
        ("ElevenLabs", test_elevenlabs_api),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}:")
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "=" * 40)
    print("📊 VALIDATION RESULTS:")
    print("=" * 40)

    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name"<15"} {status}")
        if not result:
            all_passed = False

    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed!")
        print("Your Cineo AI platform is ready with full AI capabilities!")
        print("\n🚀 Start the platform:")
        print("1. Backend: python main.py")
        print("2. Frontend: cd ../frontend && npm run dev")
        print("3. Celery: celery -A main.celery_app worker --loglevel=info")
    else:
        print("⚠️  Some tests failed.")
        print("\n🔧 Fixes:")
        print("- Check your API keys in .env file")
        print("- Verify your internet connection")
        print("- Make sure required services are running")
        print("- Run setup_api_keys.py to reconfigure")

    return all_passed

if __name__ == "__main__":
    main()
