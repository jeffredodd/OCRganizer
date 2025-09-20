# AI Provider Setup Guide

This guide provides detailed instructions for setting up each AI provider with the OCRganizer system.

## OpenAI Setup

### 1. Create OpenAI Account

1. **Visit OpenAI**: Go to [https://platform.openai.com](https://platform.openai.com)
2. **Sign Up**: Create an account or sign in
3. **Verify Email**: Check your email and verify your account

### 2. Get API Key

1. **Navigate to API Keys**: Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. **Create New Key**: Click "Create new secret key"
3. **Name Your Key**: Give it a descriptive name (e.g., "PDF-Categorizer")
4. **Copy the Key**: **Important**: Copy the key immediately - you won't be able to see it again
5. **Save Securely**: Store the key in a password manager or secure location

### 3. Add Billing Information

1. **Go to Billing**: Navigate to [https://platform.openai.com/account/billing](https://platform.openai.com/account/billing)
2. **Add Payment Method**: Add a credit card or PayPal account
3. **Set Usage Limits**: Consider setting monthly spending limits for cost control

### 4. Configure in OCRganizer

```bash
# Edit your env file
nano env

# Add your OpenAI API key
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 5. Test the Setup

```bash
# Test OpenAI connection
python -c "
from src.ai_analyzer import AIAnalyzer
analyzer = AIAnalyzer(provider='openai')
print('✅ OpenAI connection successful!')
"
```

### Cost Information

- **GPT-3.5-turbo**: ~$0.002 per 1K tokens (very affordable)
- **GPT-4**: ~$0.03 per 1K tokens (higher quality, more expensive)
- **Typical cost**: $0.01-0.05 per PDF document

## Anthropic Claude Setup

### 1. Create Anthropic Account

1. **Visit Anthropic**: Go to [https://console.anthropic.com](https://console.anthropic.com)
2. **Sign Up**: Create an account with your email
3. **Verify Email**: Check your email and verify your account

### 2. Get API Key

1. **Navigate to API Keys**: Go to [https://console.anthropic.com/keys](https://console.anthropic.com/keys)
2. **Create New Key**: Click "Create Key"
3. **Name Your Key**: Give it a descriptive name (e.g., "PDF-Categorizer")
4. **Copy the Key**: **Important**: Copy the key immediately - you won't be able to see it again
5. **Save Securely**: Store the key in a password manager

### 3. Add Billing Information

1. **Go to Billing**: Navigate to [https://console.anthropic.com/billing](https://console.anthropic.com/billing)
2. **Add Payment Method**: Add a credit card
3. **Set Usage Limits**: Consider setting monthly spending limits

### 4. Configure in OCRganizer

```bash
# Edit your env file
nano env

# Add your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
```

### 5. Test the Setup

```bash
# Test Anthropic connection
python -c "
from src.ai_analyzer import AIAnalyzer
analyzer = AIAnalyzer(provider='anthropic')
print('✅ Anthropic connection successful!')
"
```

### Cost Information

- **Claude 3 Haiku**: ~$0.25 per 1M tokens (very affordable)
- **Claude 3 Sonnet**: ~$3 per 1M tokens (high quality)
- **Claude 3 Opus**: ~$15 per 1M tokens (highest quality)
- **Typical cost**: $0.01-0.10 per PDF document

## LM Studio Setup (Local/Free)

### 1. Download LM Studio

1. **Visit LM Studio**: Go to [https://lmstudio.ai](https://lmstudio.ai)
2. **Download**: Download the desktop application for your OS
3. **Install**: Follow the installation instructions

### 2. Download a Model

1. **Open LM Studio**: Launch the application
2. **Go to Models**: Click on the "Models" tab
3. **Search for Models**: Look for these recommended models:
   - **Llama 2 7B Chat** (good balance)
   - **Mistral 7B Instruct** (excellent for instructions)
   - **Code Llama 7B** (good for structured output)

### 3. Load and Start Server

1. **Load Model**: Click on a model to download and load it
2. **Start Server**: Go to "Local Server" tab
3. **Click "Start Server"**: The server will start on port 1234
4. **Note Model Name**: Copy the exact model name shown

### 4. Configure in OCRganizer

```bash
# Edit your env file
nano env

# Configure LM Studio
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
LOCAL_MODEL_NAME=your-actual-model-name-here
```

### 5. Test the Setup

```bash
# Test LM Studio connection
python -c "
from src.ai_analyzer import AIAnalyzer
analyzer = AIAnalyzer(provider='lm_studio')
print('✅ LM Studio connection successful!')
"
```

### Cost Information

- **Free**: No API costs
- **Hardware**: Requires sufficient RAM (8GB+ recommended)
- **Performance**: Slower than cloud APIs but completely private

## Provider Comparison

| Provider | Cost | Speed | Privacy | Quality | Best For |
|----------|------|-------|---------|---------|----------|
| **OpenAI** | $ | Fast | Cloud | High | Production use |
| **Anthropic** | $$ | Fast | Cloud | Very High | High-quality analysis |
| **LM Studio** | Free | Slow | Local | Good | Privacy-sensitive docs |

## Troubleshooting

### OpenAI Issues

**Error: "Invalid API key"**
- Check the key format (should start with `sk-`)
- Ensure the key is active in your OpenAI account
- Verify billing information is added

**Error: "Insufficient quota"**
- Check your usage limits in OpenAI dashboard
- Add more credits to your account
- Consider upgrading your plan

### Anthropic Issues

**Error: "Invalid API key"**
- Check the key format (should start with `sk-ant-`)
- Ensure the key is active in your Anthropic account
- Verify billing information is added

**Error: "Rate limit exceeded"**
- Anthropic has rate limits for new accounts
- Wait a few minutes and try again
- Consider upgrading your plan

### LM Studio Issues

**Error: "Connection refused"**
- Ensure LM Studio server is running
- Check the port number (default: 1234)
- Verify firewall settings

**Error: "Model not found"**
- Check the exact model name in LM Studio
- Ensure the model is fully loaded
- Try restarting the LM Studio server

## Security Best Practices

### API Key Security

1. **Never commit keys to version control**
2. **Use environment variables**
3. **Rotate keys regularly**
4. **Use different keys for different environments**
5. **Monitor usage and set alerts**

### Example Secure Setup

```bash
# .env file (never commit this)
OPENAI_API_KEY=sk-your-secret-key-here
ANTHROPIC_API_KEY=sk-ant-your-secret-key-here

# .env.example file (commit this)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Cost Optimization Tips

### OpenAI Optimization

- Use GPT-3.5-turbo for most documents (cheaper)
- Use GPT-4 only for complex documents
- Set usage limits to control costs
- Monitor usage in the OpenAI dashboard

### Anthropic Optimization

- Use Claude 3 Haiku for simple documents
- Use Claude 3 Sonnet for complex analysis
- Set usage limits to control costs
- Monitor usage in the Anthropic console

### LM Studio Optimization

- Use smaller models for faster processing
- Close other applications to free up RAM
- Use GPU acceleration if available
- Consider model quantization for memory efficiency

## Next Steps

After setting up your AI provider:

1. **Test with sample documents**: Use the test PDFs in `input_pdfs/`
2. **Configure organization patterns**: Customize folder structures
3. **Set up monitoring**: Monitor costs and usage
4. **Optimize settings**: Adjust confidence thresholds and batch sizes

## Support

- **OpenAI Support**: [https://help.openai.com](https://help.openai.com)
- **Anthropic Support**: [https://support.anthropic.com](https://support.anthropic.com)
- **LM Studio Support**: [https://lmstudio.ai/docs](https://lmstudio.ai/docs)
- **Project Issues**: [GitHub Issues](https://github.com/yourusername/OCRganizer/issues)
