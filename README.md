# OCRganizer

A production-ready document management system that automatically categorizes, renames, and organizes PDF documents using AI-powered analysis and OCR technology.

## Overview

This system processes PDF documents through a sophisticated pipeline:
1. **Text Extraction**: Uses multiple methods (pypdf, pdfplumber, OCR) for maximum compatibility
2. **AI Analysis**: Leverages OpenAI, Anthropic, or local LM Studio models to extract metadata
3. **Smart Organization**: Creates structured folder hierarchies based on company, date, and document type
4. **Flexible Interface**: Supports both web UI and command-line usage

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PDF Input     │───▶│  Text Extraction │───▶│   AI Analysis   │
│                 │    │  (pypdf/OCR)     │    │  (GPT/Claude)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│ Organized Files │◀───│ File Organization│◀────────────┘
│   /Company/     │    │ & Smart Naming   │
│   /Year/Month/  │    │                  │
└─────────────────┘    └──────────────────┘
```

## Features

- **Multi-Provider AI Support**: OpenAI GPT, Anthropic Claude, or local LM Studio
- **Robust Text Extraction**: Handles both digital and scanned PDFs with OCR fallback  
- **Intelligent Organization**: Creates `Company/Year/Month/Day` folder structures
- **Smart Naming**: Generates descriptive filenames like "Chase_Bank_Statement_2023-03-15"
- **Dual Interface**: Web UI for interactive use, CLI for automation
- **Privacy-First**: Optional local processing with LM Studio
- **Production Ready**: Comprehensive error handling, logging, and testing

## Quick Start

### Prerequisites
- Python 3.9+
- System dependencies: `poppler-utils`, `tesseract-ocr`

### Installation

```bash
# Clone and setup
git clone <repository>
cd OCRganizer

# Install system dependencies (macOS)
brew install poppler tesseract

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install poppler-utils tesseract-ocr

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp env.example env
# Edit env file with your AI provider credentials
```

### Configuration

Choose your AI provider in the `env` file:

**OpenAI (Recommended)**
```bash
OPENAI_API_KEY=your_api_key_here
```

**Anthropic Claude**
```bash
ANTHROPIC_API_KEY=your_api_key_here
```

**LM Studio (Local/Private)**
```bash
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
LOCAL_MODEL_NAME=your_model_name
```

### Usage

**Web Interface**
```bash
python app.py
# Visit http://localhost:5000
```

**Command Line**
```bash
# Process all PDFs in input_pdfs/
python cli.py

# Preview without moving files
python cli.py --dry-run

# Custom directories
python cli.py --input /path/to/pdfs --output /path/to/organized
```

## Project Structure

```
OCRganizer/
├── src/                    # Core application modules
│   ├── pdf_processor.py    # PDF text extraction and processing
│   ├── ai_analyzer.py      # AI-powered document analysis
│   ├── file_organizer.py   # File organization and naming logic
│   └── lm_studio_client.py # Local AI model integration
├── tests/                  # Comprehensive test suite
├── templates/              # Web interface templates
├── input_pdfs/            # Default input directory
├── output/                # Default organized output
├── app.py                 # Web application entry point
├── cli.py                 # Command-line interface
├── config.yaml           # Application configuration
└── requirements.txt       # Python dependencies
```

## Testing

This project uses **TinyLlama** for consistent testing across all environments (local development, CI, and production testing).

### Quick Setup

```bash
# Setup local TinyLlama (one-time setup)
./scripts/setup_local_llm.sh

# Run all tests with TinyLlama
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Testing Options

```bash
# Run all tests (uses TinyLlama)
pytest

# Run specific test categories
pytest -m "unit"        # Unit tests
pytest -m "integration" # Integration tests  
pytest -m "e2e"         # End-to-end tests

# Run specific test file
pytest tests/test_ai_analyzer.py

# Run tests in parallel
pytest -n auto

# Docker-based testing
docker-compose -f docker-compose.test.yml up --build
```

### Test Environment

- **Local Development**: Uses TinyLlama via Docker (consistent with CI)
- **GitHub Actions**: Uses TinyLlama service container
- **No API Keys Required**: TinyLlama runs locally, no external API dependencies

## Configuration

The system uses `config.yaml` for application settings and `env` for credentials:

**Key Configuration Options:**
- `organization.structure_pattern`: Folder structure template
- `organization.filename_pattern`: File naming template  
- `processing.confidence_threshold`: Minimum AI confidence for auto-processing
- `ai.preferred_provider`: Default AI provider selection

See `config.yaml` for complete options.

## Advanced Usage

**Custom Organization Patterns**
```bash
# Use custom folder structure
python cli.py --structure "{company}/{type}/{year}"

# Use custom filename pattern
python cli.py --filename "{date}_{company}_{type}"
```

**Batch Processing with Filtering**
```bash
# Only process high-confidence results
python cli.py --confidence-threshold 0.8

# Copy instead of move files
python cli.py --copy

# Save detailed results to JSON
python cli.py --json-output results.json
```
