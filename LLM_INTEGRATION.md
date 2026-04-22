# LLM Integration Summary

## Overview
Added Claude Sonnet 4.5 integration to provide AI-powered venue suggestions as an alternative to the algorithm-based approach.

## What Was Implemented

### 1. Backend Components

#### `clients/anthropic_client.py`
- Anthropic API client with prompt caching support
- Uses `claude-sonnet-4-20250514` (latest Sonnet 4.5)
- Implements ephemeral prompt caching for cost optimization

#### `services/llm_agent_service.py`
- Service layer for LLM-based venue suggestions
- Validates LLM responses (JSON structure, required keys)
- Handles errors gracefully with detailed logging

#### `prompts/system_prompts.py`
- Optimized system prompt (>1024 tokens for efficient caching)
- Detailed algorithm descriptions for 4 preference types:
  - `equidistance`: Fair travel times
  - `minimum_overall_travel_time`: Most efficient
  - `best_rating`: Highest quality
  - `affordability`: Budget-friendly
- London-specific guidance

#### `prompts/user_templates.py`
- Minimal user template (keeps prompts under token limits)
- Dynamic formatting for locations, preference, and venue type

### 2. API Changes

#### Updated `app/main.py`
- Added `AnthropicClient` and `LLMAgentService` to app lifecycle
- Updated `SuggestRequest` model with:
  - `use_llm: bool = False`
  - `preference: str = "equidistance"`
- Modified `/suggest` endpoint to support both modes:
  - Algorithm-based (existing isochrone method)
  - LLM-based (new Claude integration)
- Returns `method` field to indicate which approach was used

### 3. Frontend Updates

#### Updated `templates/index.html`
- Added toggle switch for "Use AI Suggestions"
- Added preference selector (dropdown) that appears when AI is enabled
- Updated results display to handle both formats:
  - Algorithm: `[name, rating]` tuples
  - LLM: `{venue_name, location, why, maps}` objects
- Added method badge to show which approach was used
- Improved error handling with detailed messages

### 4. Dependencies
- Added `anthropic==0.79.0` package

## Environment Setup

Add to your `.env` file:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### Via API

**LLM Mode:**
```bash
curl -X POST http://localhost:8000/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "postcodes": ["N7 8LT", "SW1A 1AA"],
    "types": ["sports pub"],
    "use_llm": true,
    "preference": "equidistance"
  }'
```

**Algorithm Mode (default):**
```bash
curl -X POST http://localhost:8000/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "postcodes": ["N7 8LT", "SW1A 1AA"],
    "types": ["restaurant", "bar"]
  }'
```

### Via Frontend
1. Enter postcodes
2. Select venue type(s)
3. Toggle "Use AI Suggestions" ON
4. Choose optimization preference
5. Click "Find Meeting Spots"

## Cost Optimization

### Prompt Caching
- System prompt is cached for 5 minutes
- Cache hits save ~90% of input token costs
- First request: ~$0.015 (with caching setup)
- Subsequent requests: ~$0.002 (cache hits)

### Best Practices
- Keep system prompt >1024 tokens for cache efficiency ✅
- Use `use_caching=True` in client calls ✅
- Monitor cache hit rate in Anthropic console

## Architecture Benefits

### Separation of Concerns
- LLM logic is isolated in dedicated service
- Easy to swap LLM providers or models
- Both approaches can coexist

### Testability
- Services can be mocked independently
- Prompts are versioned in code
- Easy to A/B test different prompts

### Extensibility
- Can add more preference types easily
- Can support multiple LLM providers
- Can implement hybrid approaches

## Future Enhancements

1. **Prompt Versioning**: Add version parameter to load different prompt variants
2. **Hybrid Mode**: Combine algorithm + LLM (use algorithm for area, LLM for ranking)
3. **Streaming**: Stream LLM responses for better UX
4. **Caching Results**: Cache LLM responses for common queries
5. **Analytics**: Track preference usage and success rates
6. **Multi-model**: Support for other LLMs (GPT-4, Gemini, etc.)

## Files Changed

```
compromeets/
├── clients/
│   └── anthropic_client.py         [NEW]
├── services/
│   └── llm_agent_service.py        [NEW]
├── prompts/
│   ├── system_prompts.py           [UPDATED]
│   └── user_templates.py           [UPDATED]
├── app/
│   ├── main.py                     [UPDATED]
│   └── templates/
│       └── index.html              [UPDATED]
├── examples/
│   └── llm_example.py              [NEW]
├── README.md                       [UPDATED]
└── pyproject.toml                  [UPDATED]
```

## Testing

Run the example script:
```bash
uv run python examples/llm_example.py
```

Or test via the web interface:
```bash
uv run fastapi dev compromeets/app/main.py
```

Then navigate to http://localhost:8000 and toggle "Use AI Suggestions".
