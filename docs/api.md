# API Documentation

This document provides detailed information about the OCRganizer API and developer interfaces.

## Core Modules

### AI Analyzer (`src.ai_analyzer`)

The AI Analyzer module provides document analysis capabilities using various AI providers.

#### Classes

##### `AIAnalyzer`

Main class for document analysis.

```python
from src.ai_analyzer import AIAnalyzer

# Initialize with OpenAI
analyzer = AIAnalyzer(provider='openai')

# Initialize with Anthropic
analyzer = AIAnalyzer(provider='anthropic')

# Initialize with LM Studio
analyzer = AIAnalyzer(provider='lm_studio')
```

**Methods:**

- `analyze_document(document: PDFDocument) -> DocumentInfo`
- `get_provider_info() -> Dict[str, Any]`

##### `DocumentInfo`

Data class for document analysis results.

```python
from src.ai_analyzer import DocumentInfo
from datetime import date

info = DocumentInfo(
    company_name="Chase Bank",
    document_type="bank statement",
    date=date(2023, 5, 15),
    confidence_score=0.95,
    suggested_name="Chase Bank Statement 2023-05-15",
    additional_metadata={"account_type": "checking"}
)
```

**Attributes:**
- `company_name: str` - Company/organization name
- `document_type: str` - Type of document
- `date: Optional[date]` - Document date
- `confidence_score: float` - AI confidence (0.0-1.0)
- `suggested_name: str` - Suggested filename
- `additional_metadata: Dict[str, Any]` - Additional information

### PDF Processor (`src.pdf_processor`)

The PDF Processor module handles text extraction from PDF documents.

#### Classes

##### `PDFProcessor`

Main class for PDF processing.

```python
from src.pdf_processor import PDFProcessor

processor = PDFProcessor()
```

**Methods:**

- `process_pdf(file_path: Path) -> PDFDocument`
- `extract_text_pypdf(pdf_path: Path) -> str`
- `extract_text_pdfplumber(pdf_path: Path) -> str`
- `extract_text_ocr(pdf_path: Path) -> str`

##### `PDFDocument`

Data class for processed PDF documents.

```python
from src.pdf_processor import PDFDocument
from pathlib import Path

doc = PDFDocument(
    file_path=Path("document.pdf"),
    text_content="Extracted text content",
    metadata={"title": "Document Title"},
    page_count=5,
    extraction_method="pypdf"
)
```

**Attributes:**
- `file_path: Path` - Path to the PDF file
- `text_content: str` - Extracted text content
- `metadata: Dict[str, Any]` - PDF metadata
- `page_count: int` - Number of pages
- `extraction_method: str` - Method used for extraction

### File Organizer (`src.file_organizer`)

The File Organizer module handles file organization and naming.

#### Classes

##### `FileOrganizer`

Main class for file organization.

```python
from src.file_organizer import FileOrganizer

organizer = FileOrganizer()
```

**Methods:**

- `organize_file(document_info: DocumentInfo, source_path: Path, output_dir: Path) -> Path`
- `generate_folder_structure(document_info: DocumentInfo) -> Path`
- `generate_filename(document_info: DocumentInfo) -> str`
- `move_file(source: Path, destination: Path) -> bool`
- `copy_file(source: Path, destination: Path) -> bool`

### Configuration (`src.config`)

The Configuration module provides centralized configuration management.

#### Classes

##### `get_config() -> Config`

Get the application configuration.

```python
from src.config import get_config

config = get_config()
print(config.organization.structure_pattern)
```

##### `Config`

Main configuration class.

**Attributes:**
- `organization: OrganizationConfig` - Organization settings
- `ai: AIConfig` - AI provider settings
- `processing: ProcessingConfig` - Processing settings
- `web: WebConfig` - Web interface settings
- `logging: LoggingConfig` - Logging settings

## Web API

### Endpoints

#### `POST /api/analyze`

Analyze a single PDF document.

**Request:**
```json
{
  "file_path": "/path/to/document.pdf",
  "provider": "openai"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "company_name": "Chase Bank",
    "document_type": "bank statement",
    "date": "2023-05-15",
    "confidence_score": 0.95,
    "suggested_name": "Chase Bank Statement 2023-05-15",
    "additional_metadata": {
      "account_type": "checking"
    }
  }
}
```

#### `POST /api/process`

Process multiple PDF documents.

**Request:**
```json
{
  "input_dir": "/path/to/input",
  "output_dir": "/path/to/output",
  "provider": "openai",
  "dry_run": false
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "source_path": "/path/to/input/doc1.pdf",
      "destination_path": "/path/to/output/Chase_Bank/2023/05/2023-05-15_Chase_Bank_Statement.pdf",
      "document_info": {
        "company_name": "Chase Bank",
        "document_type": "bank statement",
        "date": "2023-05-15",
        "confidence_score": 0.95,
        "suggested_name": "Chase Bank Statement 2023-05-15"
      }
    }
  ]
}
```

#### `GET /api/status`

Get system status.

**Response:**
```json
{
  "status": "running",
  "version": "1.0.0",
  "ai_providers": {
    "openai": "available",
    "anthropic": "available",
    "lm_studio": "unavailable"
  }
}
```

## Command Line Interface

### CLI Module (`cli.py`)

The CLI module provides command-line interface functionality.

#### Functions

##### `main()`

Main CLI entry point.

```python
from cli import main

if __name__ == "__main__":
    main()
```

#### CLI Options

- `--input PATH` - Input directory
- `--output PATH` - Output directory
- `--dry-run` - Preview changes without moving files
- `--copy` - Copy files instead of moving
- `--confidence-threshold FLOAT` - Minimum confidence threshold
- `--structure PATTERN` - Custom folder structure pattern
- `--filename PATTERN` - Custom filename pattern
- `--json-output PATH` - Save results to JSON file
- `--verbose` - Enable verbose output

## Web Application

### Flask App (`app.py`)

The Flask application provides a web interface for the system.

#### Routes

- `GET /` - Main interface
- `POST /upload` - File upload
- `POST /process` - Process uploaded files
- `GET /status` - Processing status
- `GET /download/<filename>` - Download processed files

#### Templates

- `templates/index.html` - Main interface template

## Error Handling

### Exception Classes

##### `AIAnalyzerError`

Raised when AI analysis fails.

```python
from src.ai_analyzer import AIAnalyzerError

try:
    result = analyzer.analyze_document(document)
except AIAnalyzerError as e:
    print(f"AI analysis failed: {e}")
```

##### `PDFProcessingError`

Raised when PDF processing fails.

```python
from src.pdf_processor import PDFProcessingError

try:
    doc = processor.process_pdf(file_path)
except PDFProcessingError as e:
    print(f"PDF processing failed: {e}")
```

##### `FileOrganizationError`

Raised when file organization fails.

```python
from src.file_organizer import FileOrganizationError

try:
    organizer.organize_file(document_info, source_path, output_dir)
except FileOrganizationError as e:
    print(f"File organization failed: {e}")
```

## Logging

### Logger Configuration

```python
import logging
from src.config import get_config

config = get_config()
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format=config.logging.format,
    handlers=[
        logging.FileHandler(config.logging.file),
        logging.StreamHandler()
    ]
)
```

### Log Levels

- `DEBUG` - Detailed information for debugging
- `INFO` - General information about program execution
- `WARNING` - Warning messages for potential issues
- `ERROR` - Error messages for failed operations
- `CRITICAL` - Critical errors that may cause program termination

## Testing

### Test Structure

```
tests/
├── test_ai_analyzer.py      # AI analyzer tests
├── test_pdf_processor.py     # PDF processor tests
├── test_file_organizer.py    # File organizer tests
├── test_config.py           # Configuration tests
├── test_e2e_integration.py  # End-to-end tests
└── conftest.py              # Test fixtures
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_ai_analyzer.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_ai_analyzer.py::TestAIAnalyzer::test_analyze_document
```

### Test Fixtures

```python
import pytest
from src.ai_analyzer import AIAnalyzer

@pytest.fixture
def analyzer():
    return AIAnalyzer(provider='openai')

@pytest.fixture
def sample_document():
    from src.pdf_processor import PDFDocument
    from pathlib import Path
    
    return PDFDocument(
        file_path=Path("test.pdf"),
        text_content="Sample content",
        metadata={},
        page_count=1,
        extraction_method="pypdf"
    )
```

## Performance Considerations

### Memory Usage

- PDF processing can be memory-intensive for large files
- Use batch processing for large document sets
- Consider file size limits in configuration

### Processing Speed

- AI analysis is the bottleneck in most cases
- Local models (LM Studio) are slower than cloud APIs
- Batch processing can improve throughput

### Optimization Tips

1. **Use appropriate batch sizes** based on system resources
2. **Configure timeouts** to prevent hanging requests
3. **Use efficient folder structures** for your use case
4. **Monitor memory usage** during processing
5. **Consider parallel processing** for large batches

## Security Considerations

### API Key Management

- Store API keys in environment variables
- Never commit API keys to version control
- Use different keys for different environments
- Regularly rotate API keys

### File Security

- Validate file types before processing
- Check file sizes to prevent DoS attacks
- Sanitize filenames to prevent path traversal
- Use secure file permissions

### Network Security

- Use HTTPS for cloud AI providers
- Validate SSL certificates
- Use secure communication protocols
- Implement rate limiting for API calls

## Integration Examples

### Custom Processing Pipeline

```python
from src.pdf_processor import PDFProcessor
from src.ai_analyzer import AIAnalyzer
from src.file_organizer import FileOrganizer

def custom_process_pdf(file_path, output_dir):
    # Process PDF
    processor = PDFProcessor()
    document = processor.process_pdf(file_path)
    
    # Analyze document
    analyzer = AIAnalyzer(provider='openai')
    document_info = analyzer.analyze_document(document)
    
    # Organize file
    organizer = FileOrganizer()
    destination = organizer.organize_file(
        document_info, file_path, output_dir
    )
    
    return destination
```

### Batch Processing

```python
from pathlib import Path
from src.config import get_config

def batch_process(input_dir, output_dir):
    config = get_config()
    processor = PDFProcessor()
    analyzer = AIAnalyzer(provider=config.ai.preferred_provider)
    organizer = FileOrganizer()
    
    results = []
    for pdf_file in Path(input_dir).glob("*.pdf"):
        try:
            # Process document
            document = processor.process_pdf(pdf_file)
            document_info = analyzer.analyze_document(document)
            destination = organizer.organize_file(
                document_info, pdf_file, output_dir
            )
            results.append({
                'source': pdf_file,
                'destination': destination,
                'info': document_info
            })
        except Exception as e:
            print(f"Failed to process {pdf_file}: {e}")
    
    return results
```

### Webhook Integration

```python
from flask import Flask, request, jsonify
from src.pdf_processor import PDFProcessor
from src.ai_analyzer import AIAnalyzer

app = Flask(__name__)

@app.route('/webhook/process', methods=['POST'])
def webhook_process():
    data = request.json
    file_path = data.get('file_path')
    
    if not file_path:
        return jsonify({'error': 'file_path required'}), 400
    
    try:
        # Process document
        processor = PDFProcessor()
        document = processor.process_pdf(Path(file_path))
        
        analyzer = AIAnalyzer(provider='openai')
        document_info = analyzer.analyze_document(document)
        
        return jsonify({
            'success': True,
            'result': document_info.__dict__
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed
2. **Configuration errors**: Check YAML syntax and file permissions
3. **AI provider errors**: Verify API keys and network connectivity
4. **File processing errors**: Check file permissions and formats
5. **Memory errors**: Reduce batch sizes or file sizes

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug mode in configuration
config = get_config()
config.logging.level = "DEBUG"
```

### Performance Monitoring

```python
import time
from src.config import get_config

def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper

@monitor_performance
def process_document(file_path):
    # Document processing code
    pass
```
