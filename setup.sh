#!/bin/bash

# OCRganizer Setup Script

echo "📄 OCRganizer Setup"
echo "============================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✅ Python $python_version is installed (>= 3.9 required)"
else
    echo "❌ Python $python_version is too old. Please install Python 3.9 or higher."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for OCR dependencies
echo ""
echo "Checking for OCR dependencies..."

# Check for Poppler
if command -v pdftoppm &> /dev/null; then
    echo "✅ Poppler is installed"
    pdftoppm -v 2>&1 | head -1
else
    echo "⚠️  Poppler is not installed."
    echo "   For PDF to image conversion, install it using:"
    echo "   macOS: brew install poppler"
    echo "   Ubuntu: sudo apt-get install poppler-utils"
    echo ""
fi

# Check for Tesseract OCR
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract is installed"
    tesseract --version | head -1
else
    echo "⚠️  Tesseract OCR is not installed."
    echo "   For OCR support, install it using:"
    echo "   macOS: brew install tesseract"
    echo "   Ubuntu: sudo apt-get install tesseract-ocr"
    echo ""
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p input_pdfs
mkdir -p output
mkdir -p logs
echo "✅ Directories created"

# Copy environment file
echo ""
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY or ANTHROPIC_API_KEY"
else
    echo "✅ .env file already exists"
fi

# Run tests
echo ""
echo "Running tests..."
pytest tests/ -v

echo ""
echo "================================"
echo "✅ Setup complete!"
echo ""
echo "To get started:"
echo "1. Edit .env and add your API keys"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the application: python app.py"
echo "4. Open your browser to http://localhost:5000"
echo ""
echo "Happy organizing! 📁"
