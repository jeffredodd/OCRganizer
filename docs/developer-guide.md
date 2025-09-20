# Developer Guide

This comprehensive guide will help developers understand, set up, and contribute to the OCRganizer project.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Code Architecture](#code-architecture)
- [Testing](#testing)
- [Contributing](#contributing)
- [Debugging](#debugging)
- [Performance Optimization](#performance-optimization)

## Quick Start

> 📖 **For a quick 5-minute setup, see [Quick Start Guide](quick-start.md)**

## Development Environment

### Recommended IDE Setup

#### VS Code (Recommended)

1. **Install VS Code**: [https://code.visualstudio.com](https://code.visualstudio.com)
2. **Install Python Extension**: Search for "Python" in extensions
3. **Install Recommended Extensions**:
   ```json
   {
     "recommendations": [
       "ms-python.python",
       "ms-python.black-formatter",
       "ms-python.isort",
       "ms-python.flake8",
       "ms-python.mypy",
       "ms-toolsai.jupyter"
     ]
   }
   ```

#### PyCharm

1. **Install PyCharm**: [https://www.jetbrains.com/pycharm](https://www.jetbrains.com/pycharm)
2. **Open Project**: Open the project directory
3. **Configure Interpreter**: Set Python interpreter to your virtual environment
4. **Install Plugins**: Black, isort, flake8, mypy

### Development Tools

#### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

#### Code Formatting

```bash
# Format code with black
black src tests

# Sort imports with isort
isort src tests

# Lint with flake8
flake8 src tests

# Type check with mypy
mypy src
```

### Environment Variables

Create a `.env` file for development:

```bash
# AI Provider (choose one)
OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here

# Development settings
DEBUG=True
LOG_LEVEL=DEBUG

# Test settings
TEST_MODE=True
MOCK_AI_PROVIDERS=True
```

## Project Structure

```
OCRganizer/
├── src/                          # Core application code
│   ├── __init__.py               # Package initialization
│   ├── ai_analyzer.py            # AI analysis logic
│   ├── pdf_processor.py          # PDF text extraction
│   ├── file_organizer.py         # File organization logic
│   ├── config.py                 # Configuration management
│   └── lm_studio_client.py       # Local AI integration
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Test fixtures
│   ├── test_ai_analyzer.py       # AI analyzer tests
│   ├── test_pdf_processor.py     # PDF processor tests
│   ├── test_file_organizer.py    # File organizer tests
│   ├── test_config.py            # Configuration tests
│   └── test_e2e_integration.py   # End-to-end tests
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
│   ├── version.py                # Version management
│   └── test-ci.sh               # CI testing script
├── .github/                      # GitHub workflows
│   └── workflows/
│       ├── ci.yml                # CI/CD pipeline
│       └── docs.yml              # Documentation deployment
├── templates/                    # Web interface templates
├── input_pdfs/                   # Sample input files
├── output/                       # Processed files
├── logs/                         # Log files
├── app.py                        # Web application entry point
├── cli.py                        # Command-line interface
├── config.yaml                   # Application configuration
├── pyproject.toml                # Package configuration
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container configuration
├── .pre-commit-config.yaml       # Pre-commit hooks
├── .flake8                       # Flake8 configuration
└── README.md                     # Project documentation
```

## Code Architecture

### Core Modules

#### AI Analyzer (`src/ai_analyzer.py`)

**Purpose**: Handles AI-powered document analysis

**Key Classes**:
- `AIAnalyzer`: Main analyzer class
- `DocumentInfo`: Data class for analysis results
- `AIProvider`: Protocol for AI providers

**Key Methods**:
- `analyze_document()`: Analyze a PDF document
- `get_provider_info()`: Get provider information

**Example Usage**:
```python
from src.ai_analyzer import AIAnalyzer, DocumentInfo

# Initialize analyzer
analyzer = AIAnalyzer(provider='openai')

# Analyze document
document_info = analyzer.analyze_document(pdf_document)
print(f"Company: {document_info.company_name}")
print(f"Type: {document_info.document_type}")
```

#### PDF Processor (`src/pdf_processor.py`)

**Purpose**: Extracts text from PDF documents

**Key Classes**:
- `PDFProcessor`: Main processor class
- `PDFDocument`: Data class for processed PDFs

**Key Methods**:
- `process_pdf()`: Process a PDF file
- `extract_text_pypdf()`: Extract text using pypdf
- `extract_text_ocr()`: Extract text using OCR

**Example Usage**:
```python
from src.pdf_processor import PDFProcessor
from pathlib import Path

# Initialize processor
processor = PDFProcessor()

# Process PDF
pdf_doc = processor.process_pdf(Path("document.pdf"))
print(f"Text: {pdf_doc.text_content}")
print(f"Pages: {pdf_doc.page_count}")
```

#### File Organizer (`src/file_organizer.py`)

**Purpose**: Organizes files based on analysis results

**Key Classes**:
- `FileOrganizer`: Main organizer class

**Key Methods**:
- `organize_file()`: Organize a single file
- `generate_folder_structure()`: Generate folder structure
- `generate_filename()`: Generate filename

**Example Usage**:
```python
from src.file_organizer import FileOrganizer
from src.ai_analyzer import DocumentInfo

# Initialize organizer
organizer = FileOrganizer()

# Organize file
destination = organizer.organize_file(
    document_info, 
    source_path, 
    output_dir
)
print(f"File moved to: {destination}")
```

#### Configuration (`src/config.py`)

**Purpose**: Manages application configuration

**Key Classes**:
- `Config`: Main configuration class
- `OrganizationConfig`: Organization settings
- `AIConfig`: AI provider settings

**Example Usage**:
```python
from src.config import get_config

# Get configuration
config = get_config()

# Access settings
print(f"Structure pattern: {config.organization.structure_pattern}")
print(f"AI provider: {config.ai.preferred_provider}")
```

### Design Patterns

#### Protocol-Based Design

The system uses Python protocols for AI providers:

```python
class AIProvider(Protocol):
    def analyze_document_text(self, text: str, max_tokens: int = 800) -> str:
        """Analyze document text and return JSON response."""
        ...
```

#### Dependency Injection

AI providers are injected into the analyzer:

```python
class AIAnalyzer:
    def __init__(self, provider: str):
        self.provider = provider
        self.client = self._create_client()
```

#### Error Handling

Comprehensive error handling with fallbacks:

```python
try:
    result = analyzer.analyze_document(document)
except AIAnalyzerError as e:
    logger.error(f"AI analysis failed: {e}")
    result = create_fallback_document_info(document)
```

## Testing

### Test Structure

```
tests/
├── conftest.py                   # Shared fixtures
├── test_ai_analyzer.py           # AI analyzer tests
├── test_pdf_processor.py         # PDF processor tests
├── test_file_organizer.py        # File organizer tests
├── test_config.py                # Configuration tests
└── test_e2e_integration.py       # End-to-end tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_ai_analyzer.py::TestAIAnalyzer::test_analyze_document

# Run with verbose output
pytest -v

# Run only fast tests
pytest -m "not slow"
```

### Test Categories

#### Unit Tests
- Test individual functions and classes
- Mock external dependencies
- Fast execution

#### Integration Tests
- Test component interactions
- Use real AI providers (with test keys)
- Moderate execution time

#### End-to-End Tests
- Test complete workflows
- Use real files and AI providers
- Slower execution

### Writing Tests

#### Test Fixtures

```python
@pytest.fixture
def sample_pdf_document():
    """Create a sample PDF document for testing."""
    return PDFDocument(
        file_path=Path("test.pdf"),
        text_content="Sample content",
        metadata={},
        page_count=1,
        extraction_method="pypdf"
    )
```

#### Mocking AI Providers

```python
@pytest.fixture
def mock_ai_providers():
    """Mock all AI providers for testing."""
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"company_name": "Test"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        yield mock_openai
```

#### Test Examples

```python
def test_analyze_document(mock_ai_providers, sample_pdf_document):
    """Test document analysis."""
    analyzer = AIAnalyzer(provider='openai')
    result = analyzer.analyze_document(sample_pdf_document)
    
    assert result.company_name == "Test"
    assert result.confidence_score > 0.0
```

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make changes**: Follow coding standards
4. **Write tests**: Add tests for new functionality
5. **Run tests**: Ensure all tests pass
6. **Commit changes**: Use descriptive commit messages
7. **Push to fork**: `git push origin feature/your-feature`
8. **Create pull request**: Submit PR for review

### Coding Standards

#### Python Style

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for all public functions
- Keep functions small and focused

#### Code Formatting

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Lint code
flake8 src tests

# Type check
mypy src
```

#### Commit Messages

Use conventional commit format:

```
feat: add new AI provider support
fix: resolve PDF processing error
docs: update installation guide
test: add integration tests
```

### Pull Request Guidelines

1. **Clear title**: Describe what the PR does
2. **Detailed description**: Explain changes and motivation
3. **Link issues**: Reference related issues
4. **Add tests**: Include tests for new functionality
5. **Update docs**: Update documentation if needed

### Code Review Process

#### For Contributors

- Address all review comments
- Keep commits focused and atomic
- Write clear commit messages
- Test your changes thoroughly

#### For Reviewers

- Be constructive and helpful
- Check for security issues
- Verify test coverage
- Ensure documentation is updated

## Debugging

### Common Issues

#### Import Errors

```bash
# Error: No module named 'src'
# Solution: Install in development mode
pip install -e .
```

#### Configuration Errors

```bash
# Error: Configuration not found
# Solution: Check file paths and permissions
ls -la config.yaml
```

#### AI Provider Errors

```bash
# Error: API key invalid
# Solution: Check environment variables
echo $OPENAI_API_KEY
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python cli.py --verbose

# Check log files
tail -f logs/app.log
```

### Debugging Tools

#### VS Code Debugging

1. **Set breakpoints**: Click in the gutter
2. **Start debugging**: Press F5
3. **Step through code**: Use F10, F11
4. **Inspect variables**: Hover over variables

#### PyCharm Debugging

1. **Set breakpoints**: Click in the gutter
2. **Start debugging**: Click debug button
3. **Step through code**: Use step buttons
4. **Inspect variables**: Use variables panel

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Use logger
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

## Performance Optimization

### Profiling

#### CPU Profiling

```bash
# Install profiling tools
pip install cProfile

# Profile CLI execution
python -m cProfile -o profile.stats cli.py --dry-run

# Analyze results
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

#### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler cli.py
```

### Optimization Strategies

#### Batch Processing

```python
# Process files in batches
def process_batch(files, batch_size=10):
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        process_files(batch)
```

#### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def analyze_document_cached(text: str) -> DocumentInfo:
    """Cached document analysis."""
    return analyzer.analyze_document_text(text)
```

#### Async Processing

```python
import asyncio

async def process_documents_async(documents):
    """Process documents asynchronously."""
    tasks = [analyze_document_async(doc) for doc in documents]
    results = await asyncio.gather(*tasks)
    return results
```

### Monitoring

#### Performance Metrics

```python
import time
from contextlib import contextmanager

@contextmanager
def timer(name):
    start = time.time()
    yield
    print(f"{name} took {time.time() - start:.2f} seconds")

# Usage
with timer("Document processing"):
    result = process_document(document)
```

#### Resource Monitoring

```bash
# Monitor CPU and memory
htop

# Monitor disk usage
df -h

# Monitor network usage
iftop
```

## Advanced Topics

### Custom AI Providers

```python
class CustomAIProvider:
    def analyze_document_text(self, text: str, max_tokens: int = 800) -> str:
        """Custom AI provider implementation."""
        # Your custom logic here
        return json.dumps({
            "company_name": "Custom Company",
            "document_type": "custom type",
            "confidence_score": 0.9
        })
```

### Plugin System

```python
class PluginManager:
    def __init__(self):
        self.plugins = []
    
    def register_plugin(self, plugin):
        self.plugins.append(plugin)
    
    def process_document(self, document):
        for plugin in self.plugins:
            document = plugin.process(document)
        return document
```

### API Development

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    data = request.json
    file_path = data.get('file_path')
    
    # Process document
    processor = PDFProcessor()
    document = processor.process_pdf(Path(file_path))
    
    analyzer = AIAnalyzer(provider='openai')
    result = analyzer.analyze_document(document)
    
    return jsonify(result.__dict__)
```

## Troubleshooting

### Common Development Issues

#### Virtual Environment Issues

```bash
# Error: Command not found
# Solution: Activate virtual environment
source venv/bin/activate

# Error: Package not found
# Solution: Install in development mode
pip install -e .[dev]
```

#### Import Issues

```bash
# Error: Module not found
# Solution: Check Python path
python -c "import sys; print(sys.path)"

# Error: Circular imports
# Solution: Restructure imports
```

#### Test Issues

```bash
# Error: Tests not found
# Solution: Check test discovery
pytest --collect-only

# Error: Import errors in tests
# Solution: Check test configuration
```

### Getting Help

1. **Check documentation**: Review relevant docs
2. **Search issues**: Look for similar problems
3. **Create issue**: Provide detailed information
4. **Ask community**: Use discussions or chat

### Support Channels

- **GitHub Issues**: [Project Issues](https://github.com/yourusername/OCRganizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/OCRganizer/discussions)
- **Documentation**: [Project Docs](https://yourusername.github.io/OCRganizer)

## Next Steps

After setting up your development environment:

1. **Explore the codebase**: Read through the source code
2. **Run tests**: Ensure everything works
3. **Make a small change**: Try modifying something
4. **Write a test**: Add a test for your change
5. **Submit a PR**: Contribute your changes

## Resources

- **Python Documentation**: [https://docs.python.org](https://docs.python.org)
- **Pytest Documentation**: [https://docs.pytest.org](https://docs.pytest.org)
- **Flask Documentation**: [https://flask.palletsprojects.com](https://flask.palletsprojects.com)
- **OpenAI API Documentation**: [https://platform.openai.com/docs](https://platform.openai.com/docs)
- **Anthropic API Documentation**: [https://docs.anthropic.com](https://docs.anthropic.com)
