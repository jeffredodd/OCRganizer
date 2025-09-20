# OCRganizer CLI Usage

## Quick Start

Your `.env` file is already configured with:
- ✅ OpenAI API key (or can be configured for LM Studio)
- ✅ Input directory: `/Users/jeff/Downloads/PDFs`
- ✅ Output directory: `smb://BigNas._smb._tcp.local/Games/TempDocSpot`

## AI Provider Options

### Using OpenAI (Cloud) - Current Setup
Your current configuration uses OpenAI's cloud API.

### Using LM Studio (Local/Private)
To switch to local LM Studio for privacy and offline processing:

```bash
# Edit your .env file:
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
LOCAL_MODEL_NAME=your-loaded-model-name
```

📖 **See [LM_STUDIO_SETUP.md](LM_STUDIO_SETUP.md) for detailed setup instructions**

## Simple Commands

### 1. **Preview Mode** (Recommended First)
See what would be organized without moving files:
```bash
./preview_pdfs.sh
```

### 2. **Process All PDFs**
Organize all PDFs from your input to output directory:
```bash
./process_pdfs.sh
```

### 3. **Direct CLI Usage**
```bash
# Preview what would be organized
python cli.py --dry-run

# Actually organize the files
python cli.py

# Copy files instead of moving them
python cli.py --copy

# Use Anthropic instead of OpenAI
python cli.py --provider anthropic

# Show detailed progress
python cli.py --verbose
```

## Advanced Options

### Custom Directories
```bash
python cli.py --input /path/to/your/pdfs --output /path/to/organized
```

### Custom Organization Structure
```bash
# Different folder structure
python cli.py --structure "{year}/{company}/{type}"

# Different filename pattern
python cli.py --filename "{date}_{company}_{type}"
```

### Save Results
```bash
# Save processing results to JSON
python cli.py --json-output results.json
```

### Confidence Threshold
```bash
# Only process files with high confidence (0.8+)
python cli.py --confidence-threshold 0.8
```

## Examples

### Basic Processing
```bash
# Process all PDFs using your .env settings
python cli.py
```

### Preview Before Processing
```bash
# See what would happen
python cli.py --dry-run --verbose

# Then actually do it
python cli.py --verbose
```

### Custom Settings
```bash
# Use different AI provider with custom structure
python cli.py \
  --provider anthropic \
  --structure "{company}/{type}/{year}" \
  --filename "{company}_{type}_{date}" \
  --verbose
```

## Output Structure

Files will be organized as:
```
output/
├── Chase Bank/
│   └── 2023/
│       └── 03/
│           └── 15/
│               └── Chase_Bank_statement_2023-03-15.pdf
├── Verizon/
│   └── 2023/
│       └── 04/
│           └── 01/
│               └── Verizon_phone_bill_2023-04-01.pdf
└── ...
```

## Troubleshooting

### No PDFs Found
```bash
# Check if input directory has PDFs
ls /Users/jeff/Downloads/PDFs/*.pdf
```

### API Key Issues
```bash
# Check your .env file
cat .env | grep API_KEY
```

### Permission Issues
```bash
# Make sure scripts are executable
chmod +x *.sh
```

## Results

After processing, you'll get:
- ✅ Organized files in your output directory
- 📊 `processing_results.json` with detailed results
- 📈 Summary of companies and document types found

## Next Steps

1. **Add PDFs** to `/Users/jeff/Downloads/PDFs/`
2. **Preview** with `./preview_pdfs.sh`
3. **Process** with `./process_pdfs.sh`
4. **Check results** in your output directory!

Happy organizing! 🎉
