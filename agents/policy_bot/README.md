# Policy Bot - HR Policy Assistant

A sophisticated AI-powered chatbot that answers employee questions about company policies using Retrieval-Augmented Generation (RAG) technology.

## 🚀 Features

- **Intelligent Policy Search**: Uses vector embeddings to find relevant policy information
- **Multiple Document Formats**: Supports PDF, DOCX, and TXT files
- **REST API**: Complete FastAPI-based API for integration
- **Web Interface**: Beautiful, responsive web UI for easy interaction
- **Source Citation**: Always cites which documents the answers come from
- **Health Monitoring**: Built-in health checks and statistics
- **Scalable Architecture**: Ready for production deployment

## 📋 Prerequisites

- Python 3.9+
- Google Gemini API key (get from [Google AI Studio](https://aistudio.google.com/app/apikey))
- Policy documents in PDF, DOCX, or TXT format

## 🛠️ Installation

1. **Clone or navigate to the policy_bot directory**
   ```bash
   cd /path/to/policy_bot
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your environment**
   ```bash
   cp env_template.txt .env
   # Edit .env and add your Google API key
   ```

5. **Add your policy documents**
   ```bash
   mkdir -p knowledge_base/documents
   # Copy your policy documents (PDF, DOCX, TXT) to knowledge_base/documents/
   ```

## 🚀 Quick Start

### 1. Set Up Knowledge Base

```bash
python setup_knowledge_base.py
```

This will:
- Process all documents in `knowledge_base/documents/`
- Create vector embeddings
- Build the searchable knowledge base

### 2. Test the Bot

```bash
pytest                       # offline tests (no API key or model download needed)
python test_policy_bot.py    # end-to-end check against Gemini (needs GOOGLE_API_KEY)
```

### 3. Start the Web Interface

```bash
python web_interface.py
```

Open your browser to `http://localhost:8001` and start asking questions! The web interface also serves the API under `http://localhost:8001/api`.

### 4. Use the API

```bash
python api_server.py
```

API will be available at `http://localhost:8000`

## 📚 Usage Examples

### Web Interface
Simply open the web interface and type your questions:
- "What is the company policy on remote work?"
- "How many vacation days do employees get?"
- "What is the dress code policy?"

### API Usage

The Policy Bot provides a comprehensive REST API for integration with other systems. All endpoints return JSON responses.

#### Base URL
```
http://localhost:8000
```

#### Authentication
By default no authentication is required and the server only listens on `127.0.0.1`.
Set `POLICY_BOT_API_KEY` in `.env` to require an `X-API-Key: <value>` header on `/ask`, `/stats`
and `/docs/info` (the web interface will prompt for the key). `/` and `/health` stay open for monitoring.

Questions are limited to `MAX_QUESTION_LENGTH` characters (default 1000); longer ones get a `422`.

---

## 🔌 API Endpoints Reference

### 1. Root Endpoint
**GET** `/`

Get basic API information and available endpoints.

**Response:**
```json
{
  "message": "Policy Bot API is running!",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

**Example:**
```bash
curl "http://localhost:8000/"
```

---

### 2. Ask Question
**POST** `/ask`

Submit a policy question to the bot and get an AI-generated answer.

**Request Body:**
```json
{
  "question": "string (required, min_length=1)",
  "user_id": "string (optional)"
}
```

**Response:**
```json
{
  "answer": "string",
  "status": "string",
  "timestamp": "string (ISO format)",
  "user_id": "string|null",
  "question": "string|null",
  "sources": ["list of source documents"],
  "num_sources": "integer",
  "error": "string|null"
}
```

**Examples:**

*Basic question:*
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the remote work policy?"}'
```

*Question with user ID:*
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How many vacation days do employees get?",
    "user_id": "employee123"
  }'
```

*Sample Response:*
```json
{
  "answer": "According to the employee handbook, employees are entitled to 20 vacation days per year...",
  "status": "success",
  "timestamp": "2025-10-04T10:30:00",
  "user_id": "employee123",
  "question": "How many vacation days do employees get?",
  "sources": ["employee_handbook.pdf", "vacation_policy.txt"],
  "num_sources": 2,
  "error": null
}
```

---

### 3. Health Check
**GET** `/health`

Check the overall health and status of the Policy Bot system.

**Response:**
```json
{
  "status": "string (healthy|degraded|unhealthy)",
  "knowledge_base": {
    "total_documents": "integer",
    "status": "string"
  },
  "llm_available": "boolean",
  "vectorstore_available": "boolean",
  "timestamp": "string (ISO format)",
  "error": "string|null"
}
```

**Example:**
```bash
curl "http://localhost:8000/health"
```

*Sample Response:*
```json
{
  "status": "healthy",
  "knowledge_base": {
    "total_documents": 5,
    "status": "active"
  },
  "llm_available": true,
  "vectorstore_available": true,
  "timestamp": "2025-10-04T10:30:00",
  "error": null
}
```

---

### 4. Knowledge Base Statistics
**GET** `/stats`

Get detailed statistics about the knowledge base.

**Response:**
```json
{
  "total_documents": "integer (number of indexed chunks)",
  "status": "string (active|no_vectorstore|error)"
}
```

**Example:**
```bash
curl "http://localhost:8000/stats"
```

*Sample Response:*
```json
{
  "total_documents": 5,
  "status": "active"
}
```

---

### 5. Document Information
**GET** `/docs/info`

Get information about documents currently loaded in the knowledge base.

**Response:**
```json
{
  "total_documents": "integer",
  "status": "string"
}
```

**Example:**
```bash
curl "http://localhost:8000/docs/info"
```

---

### 6. Interactive API Documentation
**GET** `/docs`

Access the automatically generated interactive API documentation (Swagger UI).

**Example:**
Open in browser: `http://localhost:8000/docs`

---

## 📋 Error Handling

All endpoints follow standard HTTP status codes:

- `200 OK` - Successful request
- `401 Unauthorized` - Missing or wrong `X-API-Key` (only when `POLICY_BOT_API_KEY` is set)
- `404 Not Found` - Endpoint not found
- `422 Unprocessable Entity` - Invalid request (e.g. empty or too-long question)
- `500 Internal Server Error` - Server error (details are logged, not returned)

**Error Response Format:**
```json
{
  "detail": "Error description"
}
```

## 🔧 API Integration Examples

### Python Requests
```python
import requests

# Ask a question
response = requests.post(
    "http://localhost:8000/ask",
    json={
        "question": "What is the dress code policy?",
        "user_id": "emp001"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Answer: {data['answer']}")
    print(f"Sources: {[s['metadata']['filename'] for s in data['sources']]}")
else:
    print(f"Error: {response.status_code}")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function askQuestion(question, userId = null) {
  try {
    const response = await axios.post('http://localhost:8000/ask', {
      question: question,
      user_id: userId
    });
    
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// Usage
askQuestion("What is the remote work policy?", "user123")
  .then(data => console.log(data.answer));
```

### cURL Scripts
```bash
#!/bin/bash
# save as ask_policy.sh

QUESTION="$1"
USER_ID="$2"

if [ -z "$QUESTION" ]; then
    echo "Usage: $0 'Your question here' [user_id]"
    exit 1
fi

PAYLOAD="{\"question\": \"$QUESTION\""
if [ ! -z "$USER_ID" ]; then
    PAYLOAD="$PAYLOAD, \"user_id\": \"$USER_ID\""
fi
PAYLOAD="$PAYLOAD}"

curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" | jq '.'
```

### Web Frontend Integration
```html
<!DOCTYPE html>
<html>
<head>
    <title>Policy Bot</title>
</head>
<body>
    <input type="text" id="question" placeholder="Ask a policy question...">
    <button onclick="askQuestion()">Ask</button>
    <div id="answer"></div>

    <script>
    async function askQuestion() {
        const question = document.getElementById('question').value;
        
        try {
            // Serve this page from an origin listed in CORS_ORIGINS
            const response = await fetch('http://localhost:8000/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question })
            });
            
            const data = await response.json();
            // Use textContent: answers and filenames must never be rendered as HTML
            const answerDiv = document.getElementById('answer');
            answerDiv.textContent = data.answer;
            const list = document.createElement('ul');
            (data.sources || []).forEach(s => {
                const li = document.createElement('li');
                li.textContent = s.metadata.filename;
                list.appendChild(li);
            });
            answerDiv.appendChild(list);
        } catch (error) {
            console.error('Error:', error);
        }
    }
    </script>
</body>
</html>
```

### Python Integration

```python
from policy_agent import get_policy_bot

# Ask a question
response = get_policy_bot().ask_question(
    "What is the company policy on remote work?",
    user_id="employee123"
)

print(response['answer'])
```

## 🏗️ Architecture

```
Policy Bot
├── policy_agent.py          # Main Policy Bot class with RAG pipeline
├── document_processor.py    # Document loading and chunking
├── api_server.py           # FastAPI REST API
├── web_interface.py        # Web UI
├── setup_knowledge_base.py # Builds the knowledge base and runs a test question
├── update_knowledge_base.py# Rebuilds the vector database (no API key needed)
├── tests/                  # Offline pytest suite
├── test_*.py               # Manual end-to-end check scripts
├── config.py               # Configuration settings
└── knowledge_base/
    ├── documents/          # Your policy documents
    └── vector_db/          # Vector database (auto-created)
```

## ⚙️ Configuration

Set environment variables in `.env` (see `env_template.txt` for the full list):

```bash
GOOGLE_API_KEY=your_google_api_key
LLM_MODEL_NAME=gemini-2.5-flash

CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CHUNKS_RETRIEVED=5

API_HOST=127.0.0.1      # use 0.0.0.0 to expose on the network
API_PORT=8000           # api_server.py
WEB_PORT=8001           # web_interface.py
CORS_ORIGINS=http://localhost:8001
POLICY_BOT_API_KEY=     # optional shared secret
```

Relative paths (`VECTOR_DB_PATH`, `KNOWLEDGE_BASE_DIR`) are resolved against the `policy_bot` folder,
so the scripts work from any working directory.

## 🔧 Development

### Adding New Documents

1. Copy new policy documents to `knowledge_base/documents/`
2. Run the setup script again (it replaces the index, so edited or removed documents are reflected):
   ```bash
   python setup_knowledge_base.py
   ```
3. Restart the API server so it picks up the rebuilt index

### Customizing the Bot

- **Prompt Engineering**: Edit the prompt template in `policy_agent.py`
- **Chunking Strategy**: Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` in `config.py`
- **Embedding Model**: Change `EMBEDDING_MODEL` in `config.py`

### Testing

```bash
# Offline automated tests
pytest

# End-to-end checks (need GOOGLE_API_KEY; test_policy_bot.py also expects a running api_server.py)
python test_policy_bot.py

# Test specific components
python -c "from policy_agent import policy_bot; print(policy_bot.health_check())"
```

## 🚀 Deployment

### Docker Deployment

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   EXPOSE 8000
   ENV API_HOST=0.0.0.0
   
   CMD ["python", "api_server.py"]
   ```

2. **Build and run:**
   ```bash
   docker build -t policy-bot .
   docker run -p 8000:8000 policy-bot
   ```

### Cloud Deployment

The Policy Bot is ready for deployment on:
- Google Cloud Run
- AWS Lambda
- Azure Container Instances
- Heroku

## 📊 Monitoring

### Health Checks

```bash
curl "http://localhost:8000/health"
```

### Statistics

```bash
curl "http://localhost:8000/stats"
```

### Logs

Logs are written to stdout; set `LOG_LEVEL` in `.env` to control verbosity.

## 🤝 Integration

### Slack Integration

```python
from slack_bolt import App
from policy_agent import get_policy_bot

app = App(token="your_slack_token")

@app.message("policy")
def handle_policy_question(message, say):
    response = get_policy_bot().ask_question(message['text'])
    say(response['answer'])
```

### Microsoft Teams Integration

Use the Bot Framework to integrate with Teams.

## 🐛 Troubleshooting

### Common Issues

1. **"No documents in knowledge base"**
   - Run `python setup_knowledge_base.py`
   - Ensure documents are in `knowledge_base/documents/`

2. **"API key not configured"**
   - Check your `.env` file
   - Verify your Google API key is correct

3. **"Vector store is empty"**
   - Re-run the setup script
   - Check document formats are supported

4. **Poor answer quality**
   - Adjust chunk size in `config.py`
   - Improve document quality
   - Fine-tune the prompt template

### Debug Mode

Set `LOG_LEVEL=DEBUG` in your `.env` file for detailed logging.

## 📈 Performance Tips

1. **Optimize Chunk Size**: Smaller chunks for specific questions, larger for general topics
2. **Use Better Embeddings**: Consider using OpenAI embeddings for better quality
3. **Cache Responses**: Implement caching for frequently asked questions
4. **Monitor Usage**: Track which questions are asked most often

## 🔒 Security

- Store API keys in environment variables
- Use HTTPS in production
- Implement rate limiting
- Add authentication for sensitive policies
- Regular security audits of policy documents

## 📝 License

This project is part of the HR Automation Multi-Agent System.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs
3. Test with the provided test suite
4. Create an issue with detailed information

---

**Happy Policy Botting! 🤖📚**
