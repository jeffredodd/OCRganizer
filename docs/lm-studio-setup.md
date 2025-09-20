# LM Studio Integration Guide

This guide shows you how to use your local Mac's LM Studio instance instead of OpenAI's cloud API for document analysis.

## Prerequisites

1. **LM Studio installed** on your Mac
2. **A suitable model loaded** in LM Studio (recommended: Llama 2 7B, Mistral 7B, or similar)
3. **LM Studio server running** with API enabled

## Step 1: Configure LM Studio

1. **Open LM Studio** on your Mac
2. **Load a Model**: Download and load a suitable model (e.g., `microsoft/DialoGPT-medium`, `mistralai/Mistral-7B-Instruct-v0.1`)
3. **Start the Server**:
   - Go to the "Local Server" tab
   - Click "Start Server"
   - Note the port (usually `1234`)
   - Ensure "Cross-Origin Resource Sharing (CORS)" is enabled if needed

## Step 2: Configure Your Environment

Edit your `.env` file:

```bash
# Comment out or remove OpenAI cloud configuration
# OPENAI_API_KEY=your_openai_api_key_here

# Add LM Studio configuration
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
LOCAL_MODEL_NAME=your-loaded-model-name
```

**Important**: Replace `your-loaded-model-name` with the actual model name shown in LM Studio.

## Step 3: Find Your Model Name

In LM Studio:
1. Go to "Local Server" tab
2. Look for the model name in the "Loaded Model" section
3. Common formats:
   - `microsoft/DialoGPT-medium`
   - `mistralai/Mistral-7B-Instruct-v0.1`
   - `TheBloke/Llama-2-7B-Chat-GGML`

## Step 4: Test the Configuration

Run a quick test:

```bash
# Test with preview mode
./preview_pdfs.sh
```

You should see log messages indicating:
```
Using local LM Studio instance at http://localhost:1234/v1
Using model: your-loaded-model-name
```

## Recommended Models for Document Analysis

### **Best Performance** (if your Mac can handle it):
- **Llama 2 13B Chat** - Excellent reasoning
- **Mistral 7B Instruct** - Good balance of speed/quality
- **Code Llama 7B** - Good for structured output

### **Good Performance** (lighter weight):
- **Llama 2 7B Chat** - Reliable, well-tested
- **Vicuna 7B** - Good instruction following
- **OpenHermes 2.5 7B** - Good for JSON output

### **Fast Performance** (for older Macs):
- **TinyLlama 1.1B** - Very fast but less accurate
- **Phi-2 2.7B** - Good reasoning for size

## Configuration Examples

### For Llama 2 7B Chat:
```bash
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
LOCAL_MODEL_NAME=llama-2-7b-chat
OPENAI_MODEL=llama-2-7b-chat
```

### For Mistral 7B Instruct:
```bash
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
LOCAL_MODEL_NAME=mistral-7b-instruct-v0.1
OPENAI_MODEL=mistral-7b-instruct-v0.1
```

## Troubleshooting

### **Connection Issues**
- Ensure LM Studio server is running
- Check the port number (default: 1234)
- Verify firewall isn't blocking the connection

### **Model Not Found**
- Check the exact model name in LM Studio
- Update `LOCAL_MODEL_NAME` in your `.env` file
- Some models may use different naming conventions

### **Poor Results**
- Try a larger model if your Mac can handle it
- Adjust temperature settings in the code (currently 0.3)
- Ensure the model is designed for instruction following

### **Performance Issues**
- Use GPU acceleration if available
- Consider a smaller model for faster processing
- Adjust `max_tokens` if responses are being cut off

## Benefits of Using LM Studio

✅ **Privacy**: All processing happens locally on your Mac
✅ **No API Costs**: No charges for API usage
✅ **Offline Operation**: Works without internet connection
✅ **Customization**: Use any compatible model you prefer
✅ **Speed**: Can be faster than cloud APIs (depending on your hardware)

## Switching Back to OpenAI

To switch back to OpenAI's cloud service:

```bash
# Restore OpenAI configuration
OPENAI_API_KEY=your_actual_openai_key
# OPENAI_BASE_URL=http://localhost:1234/v1  # Comment out
```

## Performance Tips

1. **Use GPU acceleration** in LM Studio if available
2. **Close other applications** to free up RAM for the model
3. **Use smaller models** for faster processing of large batches
4. **Monitor CPU/GPU usage** to find the right balance

Your OCRganizer will now use your local LM Studio instance for all document analysis! 🚀
