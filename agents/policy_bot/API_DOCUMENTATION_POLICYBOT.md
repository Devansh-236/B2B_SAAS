# Policy Bot API Documentation

Complete reference for the Policy Bot REST API endpoints and integration examples.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL & Configuration](#base-url--configuration)
- [API Endpoints](#api-endpoints)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Integration Examples](#integration-examples)
- [SDKs and Libraries](#sdks-and-libraries)
- [Testing](#testing)
- [Production Considerations](#production-considerations)

## Overview

The Policy Bot API is a RESTful service built with FastAPI that provides intelligent policy question answering using RAG (Retrieval-Augmented Generation) technology. The API allows you to:

- Submit policy questions and receive AI-generated answers
- Check system health and status
- Get knowledge base statistics
- Access document information
- Monitor system performance

## Authentication

**Default**: No authentication; the server listens on `127.0.0.1` only.
**Optional API key**: set `POLICY_BOT_API_KEY` to require an `X-API-Key` header on `/ask`, `/stats` and `/docs/info`.
`/` and `/health` remain open for monitoring.

```bash
curl "http://localhost:8000/health"
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $POLICY_BOT_API_KEY" \
  -d '{"question": "What is the vacation policy?"}'
```

## Base URL & Configuration

**Development**: `http://localhost:8000`  
**Production**: Configure via environment variables

### Environment Variables

```bash
API_HOST=127.0.0.1        # Server host (0.0.0.0 to expose on the network)
API_PORT=8000             # Server port
GOOGLE_API_KEY=your_key   # Required for LLM functionality
CORS_ORIGINS=http://localhost:8001   # Comma-separated allowed browser origins
POLICY_BOT_API_KEY=       # Optional shared secret for X-API-Key
MAX_QUESTION_LENGTH=1000  # Longer questions are rejected with 422
```

## API Endpoints

### 1. Root Information
**Endpoint**: `GET /`  
**Description**: Get basic API information and available endpoints

#### Response
```json
{
  "message": "Policy Bot API is running!",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

#### Example
```bash
curl -X GET "http://localhost:8000/" \
  -H "Accept: application/json"
```

---

### 2. Ask Question
**Endpoint**: `POST /ask`  
**Description**: Submit a policy question and receive an AI-generated answer

#### Request Body
```json
{
  "question": "string",      // Required: The policy question (min_length=1)
  "user_id": "string"        // Optional: User identifier for tracking
}
```

#### Response
```json
{
  "answer": "string",           // The AI-generated answer
  "status": "string",           // Response status (success/error)
  "timestamp": "string",        // ISO format timestamp
  "user_id": "string|null",     // User ID if provided
  "question": "string|null",    // Original question
  "sources": [                  // Retrieved policy excerpts
    {"content": "string", "metadata": {"filename": "string"}}
  ],
  "num_sources": "integer"      // Number of sources used
}
```

#### Examples

**Basic Question:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the company vacation policy?"
  }'
```

**Question with User ID:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can I work remotely?",
    "user_id": "emp_12345"
  }'
```

**Sample Response:**
```json
{
  "answer": "According to the employee handbook, employees are entitled to 15 vacation days per year during their first year of employment, increasing to 20 days after one year of service. Vacation time must be requested at least 2 weeks in advance and approved by your direct supervisor.",
  "status": "success",
  "timestamp": "2025-10-04T14:30:00.123456",
  "user_id": "emp_12345",
  "question": "What is the company vacation policy?",
  "sources": [
    {"content": "Full-time employees receive 20 vacation days per year...", "metadata": {"filename": "employee_handbook.pdf"}},
    {"content": "Vacation requests must be submitted two weeks in advance...", "metadata": {"filename": "vacation_policy.txt"}}
  ],
  "num_sources": 2
}
```

---

### 3. Health Check
**Endpoint**: `GET /health`  
**Description**: Check system health and component status

#### Response
```json
{
  "status": "string",              // "healthy", "degraded" (no documents indexed) or "unhealthy"
  "knowledge_base": {
    "total_documents": "integer",  // Number of documents in knowledge base
    "status": "string"             // Knowledge base status
  },
  "llm_available": "boolean",      // LLM service availability
  "vectorstore_available": "boolean", // Vector database availability
  "timestamp": "string",           // ISO format timestamp
  "error": "string|null"           // Error details if unhealthy
}
```

#### Example
```bash
curl -X GET "http://localhost:8000/health" \
  -H "Accept: application/json"
```

**Sample Response:**
```json
{
  "status": "healthy",
  "knowledge_base": {
    "total_documents": 8,
    "status": "active"
  },
  "llm_available": true,
  "vectorstore_available": true,
  "timestamp": "2025-10-04T14:30:00.123456",
  "error": null
}
```

---

### 4. Knowledge Base Statistics
**Endpoint**: `GET /stats`  
**Description**: Get detailed knowledge base statistics

#### Response
```json
{
  "total_documents": "integer",    // Number of indexed chunks
  "status": "string"               // active | no_vectorstore | error
}
```

#### Example
```bash
curl -X GET "http://localhost:8000/stats" \
  -H "Accept: application/json"
```

**Sample Response:**
```json
{
  "total_documents": 8,
  "status": "active"
}
```

---

### 5. Document Information
**Endpoint**: `GET /docs/info`  
**Description**: Get information about loaded documents

#### Response
```json
{
  "total_documents": "integer",    // Number of indexed chunks
  "status": "string"               // Knowledge base status
}
```

#### Example
```bash
curl -X GET "http://localhost:8000/docs/info" \
  -H "Accept: application/json"
```

---

### 6. Interactive Documentation
**Endpoint**: `GET /docs`  
**Description**: Access Swagger UI for interactive API testing

Open in browser: `http://localhost:8000/docs`

---

---

## Data Models

### QuestionRequest
```python
{
  "question": str,      # Required, min_length=1
  "user_id": str|None   # Optional
}
```

### QuestionResponse
```python
{
  "answer": str,
  "status": str,
  "timestamp": str,
  "user_id": str|None,
  "question": str|None,
  "sources": list|None,
  "num_sources": int|None
}
```

### HealthResponse
```python
{
  "status": str,
  "knowledge_base": dict,
  "llm_available": bool,
  "vectorstore_available": bool,
  "timestamp": str,
  "error": str|None
}
```

## Error Handling

### HTTP Status Codes
- `200 OK` - Successful request
- `401 Unauthorized` - Missing or wrong `X-API-Key` (only when `POLICY_BOT_API_KEY` is set)
- `404 Not Found` - Endpoint not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "detail": "string"      // Error description (a list of field errors for 422)
}
```

### Common Error Scenarios

**Missing Question:**
```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Empty Question:**
```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**Server Error:**
```json
{
  "detail": "Internal server error"
}
```
Internal details are logged on the server, not returned to clients.

## Rate Limiting

**Current Version**: No rate limiting implemented  
**Recommendation**: Implement rate limiting for production use

```python
# Example rate limiting configuration
RATE_LIMIT = "100 requests per minute per IP"
```

## Integration Examples

### Python with Requests
```python
import requests
import json
from typing import Optional, Dict, Any

class PolicyBotClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def ask_question(self, question: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Ask a policy question."""
        payload = {"question": question}
        if user_id:
            payload["user_id"] = user_id
        
        response = self.session.post(
            f"{self.base_url}/ask",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        response = self.session.get(f"{self.base_url}/stats")
        response.raise_for_status()
        return response.json()

# Usage example
client = PolicyBotClient()

try:
    # Ask a question
    result = client.ask_question(
        "What is the dress code policy?",
        user_id="employee_123"
    )
    print(f"Answer: {result['answer']}")
    print(f"Sources: {result['sources']}")
    
    # Check health
    health = client.health_check()
    print(f"System status: {health['status']}")
    
except requests.exceptions.RequestException as e:
    print(f"API Error: {e}")
```

### JavaScript/Node.js with Axios
```javascript
const axios = require('axios');

class PolicyBotClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
    
    async askQuestion(question, userId = null) {
        try {
            const payload = { question };
            if (userId) payload.user_id = userId;
            
            const response = await this.client.post('/ask', payload);
            return response.data;
        } catch (error) {
            throw new Error(`API Error: ${error.response?.data?.detail || error.message}`);
        }
    }
    
    async healthCheck() {
        try {
            const response = await this.client.get('/health');
            return response.data;
        } catch (error) {
            throw new Error(`Health check failed: ${error.message}`);
        }
    }
    
    async getStats() {
        try {
            const response = await this.client.get('/stats');
            return response.data;
        } catch (error) {
            throw new Error(`Stats request failed: ${error.message}`);
        }
    }
}

// Usage example
(async () => {
    const client = new PolicyBotClient();
    
    try {
        // Ask a question
        const result = await client.askQuestion(
            "What are the company benefits?",
            "user_456"
        );
        console.log('Answer:', result.answer);
        console.log('Sources:', result.sources);
        
        // Check health
        const health = await client.healthCheck();
        console.log('System status:', health.status);
        
    } catch (error) {
        console.error('Error:', error.message);
    }
})();
```

### Go Example
```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "time"
)

type PolicyBotClient struct {
    BaseURL string
    Client  *http.Client
}

type QuestionRequest struct {
    Question string `json:"question"`
    UserID   string `json:"user_id,omitempty"`
}

type QuestionResponse struct {
    Answer     string   `json:"answer"`
    Status     string   `json:"status"`
    Timestamp  string   `json:"timestamp"`
    UserID     *string  `json:"user_id"`
    Question   *string  `json:"question"`
    Sources    []Source `json:"sources"`
    NumSources *int     `json:"num_sources"`
}

type Source struct {
    Content  string `json:"content"`
    Metadata struct {
        Filename string `json:"filename"`
    } `json:"metadata"`
}

func NewPolicyBotClient(baseURL string) *PolicyBotClient {
    return &PolicyBotClient{
        BaseURL: baseURL,
        Client: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

func (c *PolicyBotClient) AskQuestion(question, userID string) (*QuestionResponse, error) {
    req := QuestionRequest{
        Question: question,
        UserID:   userID,
    }
    
    jsonData, err := json.Marshal(req)
    if err != nil {
        return nil, err
    }
    
    resp, err := c.Client.Post(
        c.BaseURL+"/ask",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result QuestionResponse
    err = json.NewDecoder(resp.Body).Decode(&result)
    return &result, err
}

// Usage
func main() {
    client := NewPolicyBotClient("http://localhost:8000")
    
    response, err := client.AskQuestion("What is the remote work policy?", "emp001")
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    
    fmt.Printf("Answer: %s\n", response.Answer)
    fmt.Printf("Sources: %v\n", response.Sources)
}
```

### PHP Example
```php
<?php

class PolicyBotClient {
    private $baseUrl;
    
    public function __construct($baseUrl = 'http://localhost:8000') {
        $this->baseUrl = $baseUrl;
    }
    
    public function askQuestion($question, $userId = null) {
        $data = ['question' => $question];
        if ($userId) {
            $data['user_id'] = $userId;
        }
        
        $options = [
            'http' => [
                'header' => "Content-Type: application/json\r\n",
                'method' => 'POST',
                'content' => json_encode($data)
            ]
        ];
        
        $context = stream_context_create($options);
        $result = file_get_contents($this->baseUrl . '/ask', false, $context);
        
        if ($result === FALSE) {
            throw new Exception('API request failed');
        }
        
        return json_decode($result, true);
    }
    
    public function healthCheck() {
        $result = file_get_contents($this->baseUrl . '/health');
        return json_decode($result, true);
    }
}

// Usage
$client = new PolicyBotClient();

try {
    $response = $client->askQuestion(
        "What is the vacation policy?",
        "employee_789"
    );
    
    echo "Answer: " . $response['answer'] . "\n";
    echo "Sources: " . implode(', ', $response['sources']) . "\n";
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

## SDKs and Libraries

### Recommended HTTP Libraries

**Python:**
- `requests` - Simple HTTP library
- `httpx` - Async HTTP client
- `aiohttp` - Async HTTP client/server

**JavaScript/Node.js:**
- `axios` - Promise-based HTTP client
- `fetch` - Native browser/Node.js
- `node-fetch` - Node.js fetch implementation

**Java:**
- `OkHttp` - HTTP client
- `Apache HttpClient` - HTTP components
- `Spring WebClient` - Reactive HTTP client

**C#:**
- `HttpClient` - .NET HTTP client
- `RestSharp` - REST API client

## Testing

### Manual Testing with cURL
```bash
# Test health endpoint
curl -X GET "http://localhost:8000/health"

# Test question endpoint
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the dress code?"}'

# Test with invalid data
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'
```

### Automated Testing Script
```bash
#!/bin/bash
# api_test.sh

BASE_URL="http://localhost:8000"

echo "Testing Policy Bot API..."

# Test health endpoint
echo "1. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
echo "Health: $HEALTH_RESPONSE"

# Test stats endpoint
echo "2. Testing stats endpoint..."
STATS_RESPONSE=$(curl -s "$BASE_URL/stats")
echo "Stats: $STATS_RESPONSE"

# Test question endpoint
echo "3. Testing question endpoint..."
QUESTION_RESPONSE=$(curl -s -X POST "$BASE_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the remote work policy?", "user_id": "test_user"}')
echo "Question Response: $QUESTION_RESPONSE"

echo "API testing complete!"
```

### Load Testing with Apache Bench
```bash
# Test 100 requests with concurrency of 10
ab -n 100 -c 10 -H "Content-Type: application/json" \
  -p question.json http://localhost:8000/ask

# question.json content:
# {"question": "What is the vacation policy?"}
```

## Production Considerations

### Security
- Implement authentication (JWT tokens, API keys)
- Add rate limiting
- Use HTTPS in production
- Validate and sanitize all inputs
- Implement proper CORS policies

### Performance
- Add caching for frequent questions
- Implement connection pooling
- Use async request handling
- Monitor response times
- Scale horizontally with load balancers

### Monitoring
- Add logging for all API calls
- Implement health checks
- Monitor system resources
- Set up alerts for failures
- Track API usage metrics

### Configuration
```yaml
# production.yml
api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  
security:
  api_key_required: true
  rate_limit: "100/minute"
  cors_origins: ["https://yourdomain.com"]
  
logging:
  level: "INFO"
  format: "json"
  
monitoring:
  health_check_interval: 30
  metrics_enabled: true
```

### Deployment
```dockerfile
# Dockerfile for production
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## Support and Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure the API server is running
   - Check the port configuration
   - Verify firewall settings

2. **Invalid API Response**
   - Check request format
   - Verify required fields
   - Review error messages

3. **Slow Response Times**
   - Monitor system resources
   - Check document processing status
   - Consider caching frequently asked questions

### Getting Help

- Check the interactive documentation at `/docs`
- Review server logs for detailed error information
- Test endpoints individually to isolate issues
- Verify environment configuration

For more information, see the main README.md file.