# Configuration Reference

This document provides detailed information about configuring the OCRganizer system.

## Configuration Files

The system uses multiple configuration files:

1. **`env`** - Environment variables and secrets
2. **`config.yaml`** - Application settings
3. **`pyproject.toml`** - Package configuration

## Environment Variables (`env`)

> 📖 **For detailed AI provider setup instructions, see [AI Provider Setup](ai-provider-setup.md)**

### Optional Environment Variables

```bash
# Logging level
LOG_LEVEL=INFO

# Default input/output directories
DEFAULT_INPUT_DIR=input_pdfs
DEFAULT_OUTPUT_DIR=output

# AI provider selection
PREFERRED_AI_PROVIDER=openai
```

## Application Configuration (`config.yaml`)

### Organization Settings

```yaml
organization:
  # Folder structure pattern
  structure_pattern: "{company}/{year}/{month}"
  
  # Filename pattern
  filename_pattern: "{date}_{company}_{type}"
  
  # Minimum confidence for auto-processing
  confidence_threshold: 0.7
  
  # Create year-only folders for incomplete dates
  create_year_folders: true
  
  # Create month-only folders for incomplete dates
  create_month_folders: true
```

### AI Settings

```yaml
ai:
  # Preferred AI provider (openai, anthropic, lm_studio)
  preferred_provider: "openai"
  
  # Maximum tokens for AI analysis
  max_tokens: 800
  
  # Temperature for AI responses (0.0-1.0)
  temperature: 0.1
  
  # Retry attempts for failed AI calls
  retry_attempts: 3
  
  # Timeout for AI requests (seconds)
  timeout_seconds: 30
```

### Processing Settings

```yaml
processing:
  # Number of files to process in each batch
  batch_size: 10
  
  # Maximum file size (MB)
  max_file_size: 50
  
  # Enable OCR for scanned documents
  enable_ocr: true
  
  # OCR language (ISO 639-1 code)
  ocr_language: "eng"
  
  # Text extraction methods to try
  extraction_methods:
    - "pypdf"
    - "pdfplumber"
    - "ocr"
```

### Web Interface Settings

```yaml
web:
  # Host for web interface
  host: "0.0.0.0"
  
  # Port for web interface
  port: 5000
  
  # Enable debug mode
  debug: false
  
  # Maximum file upload size (MB)
  max_upload_size: 100
  
  # Allowed file extensions
  allowed_extensions: [".pdf"]
```

### Logging Settings

```yaml
logging:
  # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  level: "INFO"
  
  # Log file path
  file: "logs/app.log"
  
  # Maximum log file size (MB)
  max_size: 10
  
  # Number of backup log files
  backup_count: 5
  
  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Pattern Variables

### Folder Structure Patterns

Available variables for `structure_pattern`:

- `{company}` - Company/organization name
- `{year}` - Document year
- `{month}` - Document month (01-12)
- `{day}` - Document day (01-31)
- `{type}` - Document type
- `{date}` - Full date (YYYY-MM-DD)

**Examples:**
```yaml
# Default: Company/Year/Month
structure_pattern: "{company}/{year}/{month}"

# By document type: Company/Type/Year
structure_pattern: "{company}/{type}/{year}"

# Year-first: Year/Company/Month
structure_pattern: "{year}/{company}/{month}"

# Flat structure: All files in one folder
structure_pattern: ""
```

### Filename Patterns

Available variables for `filename_pattern`:

- `{date}` - Full date (YYYY-MM-DD)
- `{year}` - Year (YYYY)
- `{month}` - Month (MM)
- `{day}` - Day (DD)
- `{company}` - Company name
- `{type}` - Document type
- `{original}` - Original filename (without extension)

**Examples:**
```yaml
# Default: Date_Company_Type
filename_pattern: "{date}_{company}_{type}"

# Company-first: Company_Type_Date
filename_pattern: "{company}_{type}_{date}"

# Detailed: Year_Month_Day_Company_Type
filename_pattern: "{year}_{month}_{day}_{company}_{type}"

# Simple: Company_Type
filename_pattern: "{company}_{type}"
```

## Advanced Configuration

### Custom AI Prompts

You can customize the AI prompts used for document analysis:

```yaml
ai:
  prompts:
    openai:
      system: "You are a document analysis expert..."
      user: "Analyze this document and extract..."
    
    anthropic:
      system: "You are a document analysis expert..."
      user: "Analyze this document and extract..."
```

### File Processing Rules

```yaml
processing:
  rules:
    # Skip files smaller than this (bytes)
    min_file_size: 1024
    
    # Skip files larger than this (bytes)
    max_file_size: 52428800
    
    # File patterns to skip
    skip_patterns:
      - "*.tmp"
      - "*.temp"
      - ".*"
    
    # File patterns to include
    include_patterns:
      - "*.pdf"
```

### Error Handling

```yaml
error_handling:
  # Continue processing on individual file errors
  continue_on_error: true
  
  # Maximum consecutive errors before stopping
  max_consecutive_errors: 5
  
  # Retry failed files
  retry_failed: true
  
  # Log all errors to file
  log_errors: true
```

## Configuration Validation

The system validates configuration on startup:

### Required Settings
- AI provider API key
- Valid folder structure pattern
- Valid filename pattern

### Optional Settings
- Logging configuration
- Processing limits
- Web interface settings

### Validation Errors

Common validation errors and solutions:

**"Invalid structure pattern"**
- Check for valid variable names
- Ensure proper syntax

**"Invalid filename pattern"**
- Check for valid variable names
- Avoid invalid filename characters

**"Missing API key"**
- Ensure API key is set in `env` file
- Check for typos in variable names

## Environment-Specific Configuration

### Development Environment

```yaml
# config.dev.yaml
logging:
  level: "DEBUG"

web:
  debug: true

processing:
  batch_size: 1
```

### Production Environment

```yaml
# config.prod.yaml
logging:
  level: "INFO"

web:
  debug: false

processing:
  batch_size: 20
```

### Testing Environment

```yaml
# config.test.yaml
ai:
  preferred_provider: "mock"

processing:
  batch_size: 1
  enable_ocr: false
```

## Configuration Overrides

### Command Line Overrides

```bash
# Override confidence threshold
python cli.py --confidence-threshold 0.8

# Override folder structure
python cli.py --structure "{company}/{type}"

# Override filename pattern
python cli.py --filename "{company}_{type}_{date}"
```

### Environment Variable Overrides

```bash
# Override AI provider
export PREFERRED_AI_PROVIDER=anthropic

# Override confidence threshold
export CONFIDENCE_THRESHOLD=0.8

# Override batch size
export BATCH_SIZE=5
```

## Configuration Examples

### Basic Setup

```yaml
# config.yaml
organization:
  structure_pattern: "{company}/{year}/{month}"
  filename_pattern: "{date}_{company}_{type}"
  confidence_threshold: 0.7

ai:
  preferred_provider: "openai"
  max_tokens: 800
  temperature: 0.1

processing:
  batch_size: 10
  enable_ocr: true
```

### Advanced Setup

```yaml
# config.yaml
organization:
  structure_pattern: "{company}/{type}/{year}"
  filename_pattern: "{year}_{month}_{day}_{company}_{type}"
  confidence_threshold: 0.8
  create_year_folders: true
  create_month_folders: true

ai:
  preferred_provider: "anthropic"
  max_tokens: 1200
  temperature: 0.2
  retry_attempts: 5
  timeout_seconds: 60

processing:
  batch_size: 20
  max_file_size: 100
  enable_ocr: true
  ocr_language: "eng"
  extraction_methods: ["pypdf", "pdfplumber", "ocr"]

web:
  host: "0.0.0.0"
  port: 5000
  debug: false
  max_upload_size: 200

logging:
  level: "INFO"
  file: "logs/app.log"
  max_size: 20
  backup_count: 10
```

## Troubleshooting Configuration

### Common Issues

**1. Configuration not loading:**
- Check file syntax (YAML format)
- Verify file permissions
- Check for typos in variable names

**2. Environment variables not working:**
- Ensure `env` file exists
- Check variable names match exactly
- Restart the application after changes

**3. Pattern validation errors:**
- Use valid variable names in patterns
- Check for special characters
- Test patterns with sample data

### Configuration Testing

```bash
# Test configuration loading
python -c "from src.config import get_config; print(get_config())"

# Test specific settings
python -c "from src.config import get_config; config = get_config(); print(config.organization.structure_pattern)"
```

## Best Practices

### Configuration Management

1. **Use version control** for configuration files
2. **Keep secrets in environment variables**
3. **Use different configs for different environments**
4. **Document custom configurations**
5. **Test configurations before deployment**

### Security Considerations

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Restrict file permissions** on config files
4. **Use secure communication** for remote configurations
5. **Regularly rotate API keys**

### Performance Optimization

1. **Adjust batch sizes** based on system resources
2. **Configure appropriate timeouts** for AI providers
3. **Use efficient folder structures** for your use case
4. **Monitor and adjust** based on performance metrics
5. **Cache frequently used configurations**
