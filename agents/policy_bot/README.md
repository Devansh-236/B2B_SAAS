# Policy Bot - HR Policy Assistant

A sophisticated AI-powered chatbot that answers employee questions about company policies using Retrieval-Augmented Generation (RAG) technology.

## 🚀 Features

- **Intelligent Policy Search**: Uses vector embeddings to find relevant policy information
- **Multiple Document Formats**: Supports PDF, DOCX, DOC, and TXT files
- **REST API**: Complete FastAPI-based API for integration
- **Web Interface**: Beautiful, responsive web UI for easy interaction
- **Source Citation**: Always cites which documents the answers come from
- **Health Monitoring**: Built-in health checks and statistics
- **Scalable Architecture**: Ready for production deployment

## 📋 Prerequisites

- Python 3.9+
- Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))
- Policy documents in PDF, DOCX, DOC, or TXT format

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
   # Copy your policy documents (PDF, DOCX, DOC, TXT) to knowledge_base/documents/
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
python test_policy_bot.py
```

### 3. Start the Web Interface

```bash
python web_interface.py
```

Open your browser to `http://localhost:8000` and start asking questions!

### 4. Use the API

```bash
python api_server.py
```

API will be available at `http://localhost:8000/api`

## 📚 Usage Examples

### Web Interface
Simply open the web interface and type your questions:
- "What is the company policy on remote work?"
- "How many vacation days do employees get?"
- "What is the dress code policy?"

### API Usage

**Ask a question:**
```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the remote work policy?", "user_id": "employee123"}'
```

**Check health:**
```bash
curl "http://localhost:8000/api/health"
```

**Get statistics:**
```bash
curl "http://localhost:8000/api/stats"
```

### Python Integration

```python
from policy_agent import policy_bot

# Ask a question
response = policy_bot.ask_question(
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
├── setup_knowledge_base.py # Setup script
├── test_policy_bot.py      # Test suite
├── config.py               # Configuration settings
└── knowledge_base/
    ├── documents/          # Your policy documents
    ├── vector_db/          # Vector database (auto-created)
    └── output/             # Generated reports
```

## ⚙️ Configuration

Edit `config.py` or set environment variables:

```python
# LLM Configuration
LLM_API_KEY = "your_google_api_key"
LLM_MODEL_NAME = "gemini-1.5-flash"

# Document Processing
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_CHUNKS_RETRIEVED = 5

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
```

## 🔧 Development

### Adding New Documents

1. Copy new policy documents to `knowledge_base/documents/`
2. Run the setup script again:
   ```bash
   python setup_knowledge_base.py
   ```

### Customizing the Bot

- **Prompt Engineering**: Edit the prompt template in `policy_agent.py`
- **Chunking Strategy**: Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` in `config.py`
- **Embedding Model**: Change `EMBEDDING_MODEL` in `config.py`

### Testing

```bash
# Run all tests
python test_policy_bot.py

# Test specific components
python -c "from policy_agent import policy_bot; print(policy_bot.health_check())"
```

## 🚀 Deployment

### Docker Deployment

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   EXPOSE 8000
   
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
curl "http://localhost:8000/api/health"
```

### Statistics

```bash
curl "http://localhost:8000/api/stats"
```

### Logs

Check the logs for debugging:
```bash
tail -f logs/policy_bot.log
```

## 🤝 Integration

### Slack Integration

```python
from slack_bolt import App

app = App(token="your_slack_token")

@app.message("policy")
def handle_policy_question(message, say):
    response = policy_bot.ask_question(message['text'])
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
