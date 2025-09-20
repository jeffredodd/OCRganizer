#!/bin/bash

# OCRganizer Run Script

echo "📄 Starting OCRganizer..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found."
    echo "   Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found."
    echo "   Using env.example as template..."
    cp env.example .env
    echo "   Please edit .env and add your API keys."
    echo ""
fi

# Check if API keys are set
if grep -q "your_.*_api_key_here" .env; then
    echo "⚠️  Warning: API keys are not configured in .env"
    echo "   The application will have limited functionality."
    echo ""
fi

# Create directories if they don't exist
mkdir -p input_pdfs
mkdir -p output
mkdir -p logs

# Start the application
echo "Starting Flask application..."
echo "================================"
echo "📌 Application running at: http://localhost:5000"
echo "📌 Press Ctrl+C to stop"
echo "================================"
echo ""

python app.py
