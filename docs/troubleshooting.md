# Troubleshooting Guide

This guide helps you resolve common issues with the OCRganizer system.

## Installation Issues

### Python Version Problems

**Error:** `Python 3.9+ required`

**Solution:**
```bash
# Check current Python version
python --version

# Install Python 3.9+ if needed
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11

# Use pyenv for version management
pyenv install 3.11.0
pyenv local 3.11.0
```

### Virtual Environment Issues

**Error:** `No module named 'src'`

**Solution:**
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]
```

### System Dependencies

**Error:** `Tesseract not found`

**Solution:**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
choco install tesseract
```

**Error:** `pdftoppm not found`

**Solution:**
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
choco install poppler
```

## Configuration Issues

### Environment Variables

**Error:** `API key not found`

**Solution:**
```bash
# Check if env file exists
ls -la env

# Copy example if missing
cp env.example env

# Edit with your API key
nano env
```

**Error:** `Invalid configuration`

**Solution:**
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Validate configuration
python -c "from src.config import get_config; print(get_config())"
```

### AI Provider Issues

**Error:** `OpenAI API key invalid`

**Solution:**
```bash
# Check API key format
echo $OPENAI_API_KEY

# Verify key is valid
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

**Error:** `Anthropic API key invalid`

**Solution:**
```bash
# Check API key format
echo $ANTHROPIC_API_KEY

# Verify key is valid
curl -H "x-api-key: $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/messages
```

**Error:** `LM Studio connection failed`

**Solution:**
```bash
# Check if LM Studio is running
curl http://localhost:1234/v1/models

# Verify configuration
echo $OPENAI_BASE_URL
echo $LOCAL_MODEL_NAME
```

## Processing Issues

### PDF Processing Errors

**Error:** `PDF processing failed`

**Solution:**
```bash
# Check file permissions
ls -la input_pdfs/

# Test with a simple PDF
python -c "from src.pdf_processor import PDFProcessor; p = PDFProcessor(); print(p.process_pdf('test.pdf'))"
```

**Error:** `OCR processing failed`

**Solution:**
```bash
# Check Tesseract installation
tesseract --version

# Test OCR with a simple image
tesseract test.png output.txt
```

### AI Analysis Errors

**Error:** `AI analysis failed`

**Solution:**
```bash
# Check API key
echo $OPENAI_API_KEY

# Test AI provider
python -c "from src.ai_analyzer import AIAnalyzer; a = AIAnalyzer('openai'); print('AI provider working')"
```

**Error:** `Low confidence scores`

**Solution:**
- Try different AI providers
- Adjust confidence threshold in config
- Check document quality (scanning, text clarity)
- Use higher resolution scans

### File Organization Errors

**Error:** `File organization failed`

**Solution:**
```bash
# Check output directory permissions
ls -la output/

# Test with dry run
python cli.py --dry-run

# Check disk space
df -h
```

**Error:** `Invalid filename pattern`

**Solution:**
```bash
# Check pattern syntax
python -c "from src.config import get_config; print(get_config().organization.filename_pattern)"

# Test pattern with sample data
python -c "from src.file_organizer import FileOrganizer; print('Pattern validation')"
```

## Web Interface Issues

### Flask App Errors

**Error:** `Flask app not starting`

**Solution:**
```bash
# Check port availability
lsof -i :5000

# Try different port
python app.py --port 5001

# Check Flask installation
pip install flask
```

**Error:** `File upload failed`

**Solution:**
```bash
# Check file size limits
python -c "from src.config import get_config; print(get_config().web.max_upload_size)"

# Check file permissions
ls -la input_pdfs/
```

### Browser Issues

**Error:** `Page not loading`

**Solution:**
- Check if Flask app is running
- Try different browser
- Clear browser cache
- Check firewall settings

## Performance Issues

### Slow Processing

**Symptoms:** Long processing times, high memory usage

**Solution:**
```bash
# Reduce batch size
python cli.py --batch-size 5

# Use faster AI provider
export PREFERRED_AI_PROVIDER=openai

# Check system resources
top
htop
```

### Memory Issues

**Error:** `Out of memory`

**Solution:**
```bash
# Reduce batch size in config
# Check available memory
free -h

# Process smaller files
python cli.py --max-file-size 10
```

### Network Issues

**Error:** `API timeout`

**Solution:**
```bash
# Check internet connection
ping api.openai.com

# Increase timeout in config
# Use local AI provider (LM Studio)
```

## Logging and Debugging

### Enable Debug Mode

```bash
# Set debug environment variable
export LOG_LEVEL=DEBUG

# Run with verbose output
python cli.py --verbose

# Check log files
tail -f logs/app.log
```

### Common Log Messages

**INFO:** `Processing document: document.pdf`
- Normal processing message

**WARNING:** `Low confidence score: 0.3`
- AI analysis has low confidence

**ERROR:** `AI analysis failed: API key invalid`
- AI provider authentication failed

**CRITICAL:** `Out of memory`
- System resource exhaustion

### Debug Commands

```bash
# Test configuration loading
python -c "from src.config import get_config; print(get_config())"

# Test AI provider
python -c "from src.ai_analyzer import AIAnalyzer; a = AIAnalyzer('openai'); print('AI working')"

# Test PDF processing
python -c "from src.pdf_processor import PDFProcessor; p = PDFProcessor(); print('PDF processing working')"

# Test file organization
python -c "from src.file_organizer import FileOrganizer; o = FileOrganizer(); print('File organization working')"
```

## Platform-Specific Issues

### macOS Issues

**Error:** `Permission denied`

**Solution:**
```bash
# Grant permissions to Terminal
# System Preferences > Security & Privacy > Privacy > Full Disk Access

# Check file permissions
ls -la input_pdfs/
chmod 755 input_pdfs/
```

**Error:** `Homebrew not found`

**Solution:**
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install poppler tesseract
```

### Windows Issues

**Error:** `Command not found`

**Solution:**
```bash
# Install Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install dependencies
choco install poppler tesseract
```

**Error:** `Path too long`

**Solution:**
- Use shorter directory paths
- Enable long path support in Windows
- Use WSL for development

### Linux Issues

**Error:** `Package not found`

**Solution:**
```bash
# Update package list
sudo apt-get update

# Install dependencies
sudo apt-get install poppler-utils tesseract-ocr

# For other distributions, use appropriate package manager
```

## Security Issues

### API Key Security

**Error:** `API key exposed in logs`

**Solution:**
```bash
# Check for exposed keys
grep -r "sk-" logs/
grep -r "api_key" logs/

# Use environment variables
export OPENAI_API_KEY=your_key_here
```

### File Security

**Error:** `Permission denied`

**Solution:**
```bash
# Check file permissions
ls -la input_pdfs/
ls -la output/

# Set appropriate permissions
chmod 755 input_pdfs/
chmod 755 output/
```

## Getting Help

### Self-Diagnosis

1. **Check logs:** Look for error messages in log files
2. **Test components:** Run debug commands to test each component
3. **Verify configuration:** Ensure all settings are correct
4. **Check dependencies:** Ensure all required packages are installed

### Community Support

1. **GitHub Issues:** Create an issue with detailed error information
2. **Documentation:** Check this guide and other documentation
3. **Stack Overflow:** Search for similar issues
4. **Discord/Slack:** Join community channels if available

### Reporting Issues

When reporting issues, include:

1. **Error message:** Complete error message and stack trace
2. **System information:** OS, Python version, package versions
3. **Configuration:** Relevant configuration settings
4. **Steps to reproduce:** Detailed steps to reproduce the issue
5. **Log files:** Relevant log entries

### Example Issue Report

```
Title: AI analysis failing with OpenAI API

Description:
Getting "API key invalid" error when trying to analyze documents.

Error:
```
Traceback (most recent call last):
  File "src/ai_analyzer.py", line 45, in analyze_document
    response = self.client.chat.completions.create(...)
openai.AuthenticationError: Invalid API key
```

System:
- OS: macOS 13.0
- Python: 3.11.0
- Package version: 1.0.0

Configuration:
- AI Provider: OpenAI
- API Key: sk-... (masked)

Steps to reproduce:
1. Set OPENAI_API_KEY in env file
2. Run: python cli.py --dry-run
3. Error occurs during AI analysis

Logs:
[2023-05-15 10:30:00] ERROR: AI analysis failed: Invalid API key
```

## Prevention

### Best Practices

1. **Regular updates:** Keep dependencies updated
2. **Backup configuration:** Backup your configuration files
3. **Monitor logs:** Regularly check log files for issues
4. **Test changes:** Test configuration changes before deployment
5. **Document setup:** Keep notes of your configuration

### Maintenance

1. **Clean logs:** Regularly clean old log files
2. **Update dependencies:** Keep packages updated
3. **Monitor performance:** Watch for performance degradation
4. **Backup data:** Regular backups of important data
5. **Security updates:** Apply security patches promptly
