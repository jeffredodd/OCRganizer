# User Guide

This guide provides comprehensive instructions for using the OCRganizer system.

## Getting Started

> 📖 **For installation and setup instructions, see [Quick Start Guide](quick-start.md) or [Installation Guide](installation.md)**

## Web Interface

### Starting the Web Server

```bash
python app.py
```

The web interface will be available at `http://localhost:5000`.

### Web Interface Features

- **Drag & Drop**: Upload PDFs directly to the interface
- **Batch Processing**: Process multiple files at once
- **Preview Mode**: See organization results before applying
- **Progress Tracking**: Real-time processing status
- **Configuration**: Adjust settings through the web interface

### Web Interface Usage

1. **Upload PDFs**: Drag and drop files or click to browse
2. **Configure Settings**: Adjust AI provider and processing options
3. **Preview Results**: Review suggested organization before applying
4. **Process Files**: Apply the organization to your files

## Command Line Interface

### Basic Usage

```bash
# Process all PDFs in input_pdfs/
python cli.py

# Preview without moving files
python cli.py --dry-run

# Custom input/output directories
python cli.py --input /path/to/pdfs --output /path/to/organized
```

### CLI Options

```bash
python cli.py [OPTIONS]

Options:
  --input PATH              Input directory (default: input_pdfs/)
  --output PATH             Output directory (default: output/)
  --dry-run                 Preview changes without moving files
  --copy                    Copy files instead of moving
  --confidence-threshold FLOAT  Minimum confidence for auto-processing
  --structure PATTERN       Custom folder structure pattern
  --filename PATTERN        Custom filename pattern
  --json-output PATH        Save results to JSON file
  --verbose                 Enable verbose output
  --help                    Show help message
```

### Advanced CLI Usage

**Custom Organization Patterns:**
```bash
# Use custom folder structure
python cli.py --structure "{company}/{type}/{year}"

# Use custom filename pattern
python cli.py --filename "{date}_{company}_{type}"
```

**Batch Processing with Filtering:**
```bash
# Only process high-confidence results
python cli.py --confidence-threshold 0.8

# Copy instead of move files
python cli.py --copy

# Save detailed results to JSON
python cli.py --json-output results.json
```

## Configuration

> 📖 **For detailed configuration options, see [Configuration Reference](configuration.md)**

## AI Providers

> 📖 **For detailed AI provider setup and comparison, see [AI Provider Setup](ai-provider-setup.md)**

## File Organization

### Default Structure

The system creates organized folder structures like:

```
output/
├── Chase_Bank/
│   └── 2023/
│       ├── 03/
│       │   ├── 2023-03-15_Chase_Bank_Statement.pdf
│       │   └── 2023-03-20_Chase_Bank_Credit_Card_Statement.pdf
│       └── 04/
│           └── 2023-04-15_Chase_Bank_Statement.pdf
└── Wells_Fargo/
    └── 2023/
        └── 05/
            └── 2023-05-15_Wells_Fargo_Bank_Statement.pdf
```

### Custom Patterns

You can customize the organization patterns:

**Folder Structure Patterns:**
- `{company}/{year}/{month}` - Default pattern
- `{company}/{type}/{year}` - Group by document type
- `{year}/{company}/{month}` - Year-first organization

**Filename Patterns:**
- `{date}_{company}_{type}` - Default pattern
- `{company}_{type}_{date}` - Company-first naming
- `{year}_{month}_{day}_{company}_{type}` - Detailed naming

## Troubleshooting

> 📖 **For comprehensive troubleshooting, see [Troubleshooting Guide](troubleshooting.md)**

## Best Practices

### Document Preparation

1. **Scan Quality**: Use high resolution (300 DPI minimum)
2. **File Format**: PDF format works best
3. **File Size**: Keep files under 50MB for optimal processing
4. **Text Clarity**: Ensure text is readable and not skewed

### Processing Workflow

1. **Test First**: Always use `--dry-run` for new document types
2. **Batch Processing**: Process similar documents together
3. **Review Results**: Check confidence scores before final processing
4. **Backup**: Keep original files until you're satisfied with organization

### Security Considerations

- **API Keys**: Never commit API keys to version control
- **Local Processing**: Use LM Studio for sensitive documents
- **File Permissions**: Ensure proper file permissions for output directories
- **Network Security**: Use HTTPS for cloud AI providers

## Advanced Usage

### Custom Processing

```python
from src.ai_analyzer import AIAnalyzer
from src.pdf_processor import PDFProcessor

# Custom processing workflow
analyzer = AIAnalyzer(provider='openai')
processor = PDFProcessor()

# Process a single document
doc = processor.process_pdf('document.pdf')
result = analyzer.analyze_document(doc)
print(result.suggested_name)
```

### Integration with Other Tools

The system can be integrated with other document management tools:

- **File Watchers**: Monitor directories for new PDFs
- **Cron Jobs**: Schedule regular processing
- **Webhooks**: Trigger processing from other applications
- **API Integration**: Use the core modules in other Python applications

## Support

> 📖 **For additional help, see [Troubleshooting Guide](troubleshooting.md) or create an issue on GitHub**
