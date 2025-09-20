# Quick Start Guide

Get the OCRganizer running in 5 minutes! This guide provides the essential steps to get started quickly.

## Prerequisites

- **Python 3.9+** installed on your system
- **Git** for cloning the repository
- **AI Provider API Key** (see [AI Provider Setup](ai-provider-setup.md) for detailed instructions)

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/OCRganizer.git
cd OCRganizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .[dev]
```

## Step 2: Install System Dependencies

**macOS**: `brew install poppler tesseract`  
**Ubuntu/Debian**: `sudo apt-get install poppler-utils tesseract-ocr`  
**Windows**: `choco install poppler tesseract`

> 📖 **For detailed system dependency installation, see [Installation Guide](installation.md)**

## Step 3: Configure AI Provider

**Quick setup for OpenAI (recommended for beginners):**

```bash
# Copy environment template
cp env.example env

# Edit env file and add your OpenAI API key
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-actual-api-key-here
```

> 📖 **For detailed AI provider setup (OpenAI, Anthropic, LM Studio), see [AI Provider Setup](ai-provider-setup.md)**

## Step 4: Test and Start

```bash
# Test the installation
python cli.py --dry-run

# Start processing (web interface)
python app.py
# Visit http://localhost:5000

# Or use command line
python cli.py
```

## Next Steps

- **Learn more**: Read the [User Guide](user-guide.md) for detailed usage
- **Configure**: See [Configuration Reference](configuration.md) for advanced settings
- **Troubleshoot**: Check [Troubleshooting Guide](troubleshooting.md) if you encounter issues

