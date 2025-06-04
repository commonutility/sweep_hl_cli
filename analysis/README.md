# Latency Analysis Module

This module provides comprehensive timing and latency analysis for the Hyperliquid Trading Assistant, tracking the full request lifecycle from frontend user interaction to asset page rendering.

## Overview

The analysis module tracks timing at multiple stages:

1. **Frontend Timing**
   - User submits query
   - API request sent
   - Response received
   - UI component rendering

2. **Backend Timing**
   - Request received
   - Database operations
   - LLM processing
   - OpenAI API calls
   - Response processing

## Components

### 1. TimingTracker (`timing_tracker.py`)
- Core timing collection system
- Thread-safe singleton implementation
- Tracks timing events throughout request lifecycle
- Saves data to JSON files for analysis

### 2. LatencyAnalyzer (`latency_analyzer.py`)
- Analyzes collected timing data
- Generates statistics and reports
- Identifies bottlenecks
- Provides recommendations

### 3. TimingMiddleware (`timing_middleware.py`)
- FastAPI middleware for automatic request timing
- Adds timing headers to responses
- Integrates with TimingTracker

### 4. Frontend Timing (`frontend/src/utils/timingTracker.js`)
- JavaScript timing tracker for client-side measurements
- Tracks UI rendering and user interactions
- Sends data to backend for correlation

## API Endpoints

The module adds several API endpoints for timing analysis:

- `GET /api/timing/requests` - List all tracked requests
- `GET /api/timing/request/{request_id}` - Get timing for specific request
- `GET /api/timing/stage/{stage_name}/stats` - Get statistics for a stage
- `GET /api/timing/report` - Generate comprehensive report
- `GET /api/timing/breakdown` - Get average stage breakdown
- `GET /api/timing/visualization/{request_id}` - Get visualization data

## Usage

### 1. Automatic Timing Collection

The timing middleware automatically tracks all API requests:

```python
# Already integrated in backend/main.py
app.add_middleware(TimingMiddleware)
```

### 2. Manual Timing in Code

Add custom timing stages in your code:

```python
from analysis.timing_tracker import timing_tracker

# In your endpoint or function
timing_tracker.start_stage(request_id, "custom_operation")
# ... do work ...
timing_tracker.end_stage(request_id, "custom_operation")
```

### 3. Frontend Timing

Use the frontend timing tracker:

```javascript
import timingTracker, { generateRequestId } from './utils/timingTracker';

// Start timing
const requestId = generateRequestId();
timingTracker.startRequest(requestId);

// Track stages
timingTracker.startStage(requestId, 'api_call');
const response = await fetch('/api/chat', { 
  headers: { 'X-Request-ID': requestId }
});
timingTracker.endStage(requestId, 'api_call');

// End timing
timingTracker.endRequest(requestId);
```

### 4. Generate Reports

Use the command-line tool:

```bash
# Generate JSON report
python analysis/generate_report.py

# Generate text summary
python analysis/generate_report.py --format text

# Analyze specific request
python analysis/generate_report.py --request-id <request_id> --format text
```

### 5. View Live Timing

Access timing data via API:

```bash
# List all requests
curl http://localhost:8000/api/timing/requests

# Get specific request timing
curl http://localhost:8000/api/timing/request/<request_id>

# Get comprehensive report
curl http://localhost:8000/api/timing/report
```

## Timing Stages

The system tracks these key stages:

1. **backend_processing** - Total backend processing time
2. **db_add_user_message** - Adding user message to database
3. **db_get_history** - Retrieving conversation history
4. **llm_processing** - LLM decision making
5. **openai_api_call** - OpenAI API request
6. **response_processing** - Processing LLM response
7. **db_add_assistant_message** - Saving assistant response

## Example Output

```json
{
  "request_id": "abc123",
  "total_duration_ms": 1250.5,
  "stages": {
    "backend_processing": {
      "duration_ms": 1245.3,
      "metadata": {"status_code": 200}
    },
    "llm_processing": {
      "duration_ms": 980.2,
      "metadata": {}
    },
    "openai_api_call": {
      "duration_ms": 875.1,
      "metadata": {}
    }
  },
  "bottlenecks": [
    {
      "stage": "llm_processing",
      "duration_ms": 980.2,
      "percentage": 78.4
    }
  ]
}
```

## Best Practices

1. **Use Request IDs** - Always pass X-Request-ID header from frontend
2. **Track Key Operations** - Add timing for database queries, API calls, etc.
3. **Regular Analysis** - Run reports periodically to identify trends
4. **Clean Old Data** - Remove old timing files to save space
5. **Production Considerations** - Consider disabling detailed timing in production for performance

## Troubleshooting

### Missing Timing Data
- Ensure timing middleware is added before other middleware
- Check that request IDs are properly passed
- Verify analysis/data directory exists and is writable

### High Latency
- Check OpenAI API response times
- Review database query performance
- Consider caching frequently accessed data
- Optimize LLM prompt size

### Memory Usage
- Clear old timing data regularly
- Limit number of tracked requests in memory
- Use file-based storage for long-term analysis 