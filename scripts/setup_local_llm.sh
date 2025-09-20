#!/bin/bash

# Setup script for local TinyLlama development environment
# This ensures everyone uses the same LLM setup

set -e

echo "🚀 Setting up local TinyLlama for development..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Ollama container is already running
if docker ps | grep -q "ollama"; then
    echo "✅ Ollama container already running"
else
    echo "🐳 Starting Ollama container..."
    docker run -d \
        --name ollama-dev \
        -p 11434:11434 \
        -v ollama_data:/root/.ollama \
        --restart unless-stopped \
        ollama/ollama:latest
    
    echo "⏳ Waiting for Ollama to start..."
    sleep 10
fi

# Wait for Ollama to be ready
echo "🔍 Checking if Ollama is ready..."
timeout 60 bash -c 'until curl -f http://localhost:11434/api/tags >/dev/null 2>&1; do sleep 2; done' || {
    echo "❌ Ollama failed to start within 60 seconds"
    exit 1
}

echo "✅ Ollama is ready!"

# Check if TinyLlama model is already available
if curl -s http://localhost:11434/api/tags | grep -q "tinyllama"; then
    echo "✅ TinyLlama model already available"
else
    echo "📥 Downloading TinyLlama model (this may take a few minutes)..."
    curl -X POST http://localhost:11434/api/pull \
        -H "Content-Type: application/json" \
        -d '{"name": "tinyllama"}' \
        --silent --show-error
    
    echo "⏳ Waiting for model to be ready..."
    timeout 300 bash -c 'until curl -s http://localhost:11434/api/tags | grep -q tinyllama; do sleep 5; echo "Still downloading..."; done' || {
        echo "❌ TinyLlama download timed out"
        exit 1
    }
fi

echo "✅ TinyLlama model is ready!"

# Test the setup
echo "🧪 Testing TinyLlama..."
response=$(curl -s -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{"model": "tinyllama", "prompt": "Hello", "stream": false}' \
    --max-time 30)

if echo "$response" | grep -q "response"; then
    echo "✅ TinyLlama is working correctly!"
else
    echo "❌ TinyLlama test failed"
    echo "Response: $response"
    exit 1
fi

# Create/update .env file with TinyLlama settings
echo "📝 Updating .env file..."
cat > .env << EOF
# TinyLlama Local Development Setup
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=tinyllama
LOCAL_MODEL_NAME=tinyllama

# Optional: Add your real API keys for comparison testing
# OPENAI_API_KEY_REAL=your_real_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here
EOF

echo ""
echo "🎉 Setup complete! You can now:"
echo "   1. Run tests: pytest tests/"
echo "   2. Use the CLI: python cli.py"
echo "   3. Start the web app: python app.py"
echo ""
echo "📋 TinyLlama is running at: http://localhost:11434"
echo "🔧 Environment configured in .env file"
echo ""
echo "To stop TinyLlama: docker stop ollama-dev"
echo "To restart TinyLlama: docker start ollama-dev"
