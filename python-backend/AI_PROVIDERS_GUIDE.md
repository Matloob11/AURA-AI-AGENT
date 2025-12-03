# AURA AI - Multi-Provider Setup Guide

## Overview

AURA AI now supports **multiple AI providers** with automatic fallback. If one provider fails, the system automatically tries the next available provider.

### Supported Providers

1. **OpenAI** (GPT-4, GPT-3.5-turbo)
2. **Hugging Face** (Mistral, Llama, etc.)
3. **Cohere** (Command models)
4. **Google Gemini** (Gemini Pro)
5. **Deepseek** (Deepseek Chat)

---

## Quick Start

### 1. Get API Keys

You need at least **one** API key. Get them from:

- **OpenAI**: https://platform.openai.com/api-keys
- **Hugging Face**: https://huggingface.co/settings/tokens
- **Cohere**: https://dashboard.cohere.com/api-keys
- **Google Gemini**: https://makersuite.google.com/app/apikey
- **Deepseek**: https://platform.deepseek.com/api_keys

### 2. Configure .env File

Copy `.env.example` to `.env` and add your API keys:

```env
# Add at least one API key
OPENAI_API_KEY=sk-...
HF_API_KEY=hf_...
COHERE_API_KEY=...
GEMINI_API_KEY=...
DEEPSEEK_API_KEY=...

# Optional: Configure AI behavior
AI_MODEL=gpt-4
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=500
```

### 3. Install Dependencies

```bash
cd python-backend
pip install -r requirements.txt
```

### 4. Test the System

```bash
python test_ai_fallback.py
```

---

## How Fallback Works

### Priority Order

The system tries providers in this order:

1. **OpenAI** (if key available)
2. **Hugging Face** (if key available)
3. **Cohere** (if key available)
4. **Gemini** (if key available)
5. **Deepseek** (if key available)

### Automatic Fallback

If a provider fails (network error, invalid key, rate limit), the system automatically tries the next available provider.

**Example:**
```
User: "Hello, what's the weather?"

1. Try OpenAI → ❌ Rate limit exceeded
2. Try Hugging Face → ❌ Model loading
3. Try Cohere → ✅ Success!

Response: "I'm AURA, your AI assistant..."
```

---

## Configuration Options

### AI_MODEL

Specifies which model to use (primarily for OpenAI):

```env
AI_MODEL=gpt-4          # OpenAI GPT-4
AI_MODEL=gpt-3.5-turbo  # OpenAI GPT-3.5
```

Other providers use their default models:
- Hugging Face: `mistralai/Mistral-7B-Instruct-v0.2`
- Cohere: Default Command model
- Gemini: `gemini-pro`
- Deepseek: `deepseek-chat`

### AI_TEMPERATURE

Controls response randomness (0.0 - 2.0):

```env
AI_TEMPERATURE=0.7  # Balanced (default)
AI_TEMPERATURE=0.3  # More focused
AI_TEMPERATURE=1.0  # More creative
```

### AI_MAX_TOKENS

Maximum response length:

```env
AI_MAX_TOKENS=500   # Default
AI_MAX_TOKENS=1000  # Longer responses
AI_MAX_TOKENS=200   # Shorter responses
```

---

## API Endpoints

### GET /ai/config

Get current AI configuration and provider status:

```json
{
  "status": "success",
  "config": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 500,
    "available_providers": ["openai", "cohere"],
    "last_provider_used": "openai",
    "api_keys_configured": {
      "openai": true,
      "huggingface": false,
      "cohere": true,
      "gemini": false,
      "deepseek": false
    }
  },
  "provider_stats": {
    "openai": {
      "calls": 15,
      "errors": 2,
      "avg_response_time": 1.23,
      "success_rate": 86.7
    }
  }
}
```

### POST /chat

Send a message to AI (uses automatic fallback):

```json
{
  "message": "Hello, what can you do?"
}
```

Response:
```json
{
  "response": "I'm AURA, your AI assistant...",
  "status": "success",
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## Provider-Specific Notes

### OpenAI
- **Best for**: General purpose, high quality responses
- **Cost**: Pay per token
- **Speed**: Fast (1-2 seconds)
- **Models**: GPT-4, GPT-3.5-turbo

### Hugging Face
- **Best for**: Free tier, open-source models
- **Cost**: Free (with rate limits)
- **Speed**: Variable (2-10 seconds, model loading)
- **Models**: Mistral, Llama, etc.

### Cohere
- **Best for**: Enterprise use, reliable
- **Cost**: Free tier + paid plans
- **Speed**: Fast (1-3 seconds)
- **Models**: Command, Command-Light

### Google Gemini
- **Best for**: Google ecosystem integration
- **Cost**: Free tier available
- **Speed**: Fast (1-2 seconds)
- **Models**: Gemini Pro

### Deepseek
- **Best for**: Cost-effective, OpenAI-compatible
- **Cost**: Lower than OpenAI
- **Speed**: Fast (1-2 seconds)
- **Models**: Deepseek Chat

---

## Troubleshooting

### No Providers Available

**Error**: "AI Engine not configured. Please set at least one API key..."

**Solution**: Add at least one API key to your `.env` file.

### All Providers Failed

**Error**: "All AI providers failed. Please check your API keys..."

**Possible causes**:
1. Invalid API keys
2. Network connection issues
3. All providers are rate-limited
4. API services are down

**Solution**:
1. Verify API keys are correct
2. Check internet connection
3. Wait a few minutes and try again
4. Check provider status pages

### Slow Responses

If responses are slow:
1. Check which provider is being used: `GET /ai/config`
2. Hugging Face can be slow during model loading
3. Consider using OpenAI or Cohere for faster responses

### Rate Limits

If you hit rate limits:
1. The system will automatically try the next provider
2. Add more API keys for better redundancy
3. Upgrade to paid tiers for higher limits

---

## Testing

### Run Full Test Suite

```bash
python test_ai_fallback.py
```

Tests include:
- ✓ Basic chat functionality
- ✓ Conversation history
- ✓ Provider fallback
- ✓ Individual provider tests
- ✓ Configuration retrieval
- ✓ History limit (20 messages)

### Manual Testing

```bash
# Start the server
python main.py

# In another terminal, test the chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Check configuration
curl http://localhost:8000/ai/config
```

---

## Best Practices

### 1. Configure Multiple Providers

For maximum reliability, configure at least 2-3 providers:

```env
OPENAI_API_KEY=sk-...      # Primary
COHERE_API_KEY=...         # Backup 1
GEMINI_API_KEY=...         # Backup 2
```

### 2. Monitor Provider Stats

Check `/ai/config` regularly to see:
- Which providers are being used
- Error rates
- Average response times

### 3. Adjust Temperature

- **0.3-0.5**: For factual, consistent responses
- **0.7**: Balanced (default)
- **0.9-1.2**: For creative tasks

### 4. Set Appropriate Token Limits

- **200-300**: Quick responses
- **500**: Default, good balance
- **1000+**: Detailed explanations

---

## Migration from Old System

If you're upgrading from the old OpenAI-only system:

### What Changed

1. ✅ Multiple providers supported
2. ✅ Automatic fallback
3. ✅ Provider statistics tracking
4. ✅ New API keys in `.env`

### What Stayed the Same

1. ✅ All endpoints work identically
2. ✅ Socket.IO events unchanged
3. ✅ Voice, Vision, Automation engines unchanged
4. ✅ Frontend (Electron) unchanged

### Migration Steps

1. Update `.env` with new API key fields
2. Install new dependencies: `pip install -r requirements.txt`
3. Restart the server
4. Test with: `python test_ai_fallback.py`

**No code changes needed in your frontend!**

---

## Support

For issues or questions:
1. Check the logs: Look for provider names in console output
2. Run diagnostics: `python test_ai_fallback.py`
3. Verify API keys: `GET /ai/config`

---

## License

Same as AURA AI project license.
