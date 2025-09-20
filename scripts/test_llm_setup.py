#!/usr/bin/env python3
"""
Script to test LLM setup for development and CI.

This script helps verify that your LLM setup is working correctly,
whether you're using OpenAI, Anthropic, or a local model like Ollama.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai_analyzer import AIAnalyzer
from src.pdf_processor import PDFDocument
from src.config import get_config


def test_openai_api():
    """Test OpenAI API connection."""
    print("🔍 Testing OpenAI API...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return False
    
    if api_key == 'test-key':
        print("⚠️  Using test API key - this won't work with real OpenAI")
        return False
    
    try:
        # Test with a simple request
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # For local models (Ollama), test the models endpoint
        if 'localhost' in base_url or '127.0.0.1' in base_url:
            print(f"🏠 Testing local LLM at {base_url}")
            
            # Test Ollama API
            ollama_base = base_url.replace('/v1', '').rstrip('/')
            try:
                response = requests.get(f"{ollama_base}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    print(f"✅ Local Ollama running with {len(models)} models")
                    for model in models[:3]:  # Show first 3 models
                        print(f"   - {model['name']}")
                    return True
                else:
                    print(f"❌ Ollama not responding: {response.status_code}")
                    return False
            except requests.RequestException as e:
                print(f"❌ Cannot connect to Ollama: {e}")
                return False
        
        else:
            # Test real OpenAI API
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ OpenAI API working")
                return True
            else:
                print(f"❌ OpenAI API error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False


def test_anthropic_api():
    """Test Anthropic API connection."""
    print("\n🔍 Testing Anthropic API...")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("❌ No ANTHROPIC_API_KEY found")
        return False
    
    if api_key == 'test-key':
        print("⚠️  Using test API key - this won't work with real Anthropic")
        return False
    
    try:
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 5,
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Anthropic API working")
            return True
        else:
            print(f"❌ Anthropic API error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False


def test_ai_analyzer():
    """Test the AI analyzer with current configuration."""
    print("\n🔍 Testing AI Analyzer...")
    
    try:
        # Create a test document
        test_doc = PDFDocument(
            file_path=Path("test.pdf"),
            text_content="Chase Bank Monthly Statement\nDate: January 15, 2024\nAccount: ****1234",
            metadata={"title": "Bank Statement"}
        )
        
        # Test with configured provider
        config = get_config()
        print(f"📋 Using provider: {config.ai.preferred_provider}")
        
        analyzer = AIAnalyzer()
        result = analyzer.analyze_document(test_doc)
        
        print("✅ AI Analyzer working!")
        print(f"   Company: {result.company_name}")
        print(f"   Type: {result.document_type}")
        print(f"   Date: {result.date}")
        print(f"   Confidence: {result.confidence_score}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Analyzer error: {e}")
        return False


def test_environment():
    """Test the current environment setup."""
    print("🌍 Environment Check:")
    print(f"   CI: {os.getenv('CI', 'false')}")
    print(f"   GitHub Actions: {os.getenv('GITHUB_ACTIONS', 'false')}")
    
    # Check API keys (masked)
    openai_key = os.getenv('OPENAI_API_KEY', '')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
    
    print(f"   OpenAI Key: {'✅ Set' if openai_key and len(openai_key) > 10 else '❌ Missing/Invalid'}")
    print(f"   Anthropic Key: {'✅ Set' if anthropic_key and len(anthropic_key) > 10 else '❌ Missing/Invalid'}")
    print(f"   OpenAI Base URL: {os.getenv('OPENAI_BASE_URL', 'default')}")


def main():
    """Main test function."""
    print("🚀 LLM Setup Test Script")
    print("=" * 50)
    
    test_environment()
    
    # Test APIs
    openai_ok = test_openai_api()
    anthropic_ok = test_anthropic_api()
    
    # Test AI analyzer if at least one API works
    if openai_ok or anthropic_ok:
        analyzer_ok = test_ai_analyzer()
    else:
        print("\n⚠️  Skipping AI Analyzer test - no working APIs")
        analyzer_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   OpenAI: {'✅' if openai_ok else '❌'}")
    print(f"   Anthropic: {'✅' if anthropic_ok else '❌'}")
    print(f"   AI Analyzer: {'✅' if analyzer_ok else '❌'}")
    
    if openai_ok or anthropic_ok:
        print("\n🎉 Setup looks good! You can run integration tests.")
    else:
        print("\n⚠️  No working APIs found. Unit tests will use mocks.")
    
    return openai_ok or anthropic_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
