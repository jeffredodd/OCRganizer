# Installation Guide

This guide will help you install and set up the OCRganizer system on your machine.

## Prerequisites

### System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: At least 4GB RAM (8GB recommended for local AI models)
- **Storage**: 2GB free space for dependencies

### System Dependencies

The system requires several external tools for PDF processing and OCR:

#### macOS
```bash
# Install using Homebrew
brew install poppler tesseract

# Optional: Install additional language packs
brew install tesseract-lang
```

#### Ubuntu/Debian
```bash
# Update package list
sudo apt-get update

# Install required packages
sudo apt-get install -y poppler-utils tesseract-ocr

# Optional: Install additional language packs
sudo apt-get install -y tesseract-ocr-eng tesseract-ocr-spa
```

#### Windows
```powershell
# Install using Chocolatey
choco install poppler tesseract

# Or download from:
# Poppler: https://blog.alivate.com.au/poppler-windows/
# Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
```

## Installation Methods

### Method 1: Development Installation (Recommended)

This method installs the package in development mode, allowing you to make changes to the code.

```bash
# Clone the repository
git clone https://github.com/yourusername/OCRganizer.git
cd OCRganizer

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install in development mode with all dependencies
pip install -e .[dev]

# Verify installation
python -c "import src.ai_analyzer; print('Installation successful!')"
```

### Method 2: Production Installation

For production use or if you don't need to modify the code:

```bash
# Install from PyPI (when published)
pip install OCRganizer

# Or install from GitHub
pip install git+https://github.com/yourusername/OCRganizer.git
```

### Method 3: Docker Installation

```bash
# Build the Docker image
docker build -t OCRganizer .

# Run the web interface
docker run -p 5000:5000 -v $(pwd)/input_pdfs:/app/input_pdfs OCRganizer
```

## Configuration

### 1. Environment Setup

Copy the example environment file and configure it:

```bash
cp env.example env
```

> 📖 **For detailed AI provider setup instructions, see [AI Provider Setup](ai-provider-setup.md)**

### 2. Application Configuration

The system uses `config.yaml` for application settings. For detailed configuration options, see [Configuration Reference](configuration.md).

## Verification

### Test the Installation

Run the test suite to verify everything is working:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest tests/test_pdf_processor.py  # Test specific module
```

### Test AI Provider

> 📖 **For AI provider testing instructions, see [AI Provider Setup](ai-provider-setup.md)**

### Test PDF Processing

```bash
# Test with a sample PDF
python cli.py --dry-run --input input_pdfs/
```

## Troubleshooting

> 📖 **For comprehensive troubleshooting, see [Troubleshooting Guide](troubleshooting.md)**

## Next Steps

Once installation is complete:

1. Read the [User Guide](user-guide.md) for usage instructions
2. Configure your AI provider in the `env` file
3. Test with sample PDFs in the `input_pdfs/` directory
4. Explore the [API Documentation](api.md) for advanced usage
