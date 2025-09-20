#!/bin/bash

# OCRganizer Batch Processing Script
# Uses the directories configured in .env file

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found."
    echo "   Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check for .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found."
    echo "   Please create .env with your API keys and directories."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ No API key found in .env file"
    echo "   Please set either OPENAI_API_KEY or ANTHROPIC_API_KEY"
    exit 1
fi

# Check input directory
if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ Input directory not found: $INPUT_DIR"
    echo "   Please check your INPUT_DIR setting in .env"
    exit 1
fi

# Count PDF files
PDF_COUNT=$(find "$INPUT_DIR" -name "*.pdf" | wc -l)

if [ $PDF_COUNT -eq 0 ]; then
    echo "⚠️  No PDF files found in $INPUT_DIR"
    echo "   Add some PDF files to the input directory and try again."
    exit 0
fi

echo "📁 Input: $INPUT_DIR"
echo "📁 Output: $OUTPUT_DIR"
echo "📄 Found $PDF_COUNT PDF files"
echo ""

# Ask for confirmation
read -p "🚀 Ready to process? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""

# Run the CLI tool (it will handle all the beautiful output)
python cli.py \
    --input "$INPUT_DIR" \
    --output "$OUTPUT_DIR" \
    --json-output "processing_results.json"
