# Onboarder - FastAPI-Based Employee Onboarding System

A sophisticated FastAPI-based system for automating and managing employee onboarding processes using AI agents, intelligent workflow orchestration, and proper state management with context sharing.

## 🚀 Quick Start

### Using npx (Recommended)

```bash
# Install and start the server
npx onboarder-api

# Or if you have the package installed globally
onboarder
```

### Manual Setup

```bash
# Clone and setup
git clone <repository-url>
cd Onboarder

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your GEMINI_API_KEY

# Start the server
python main.py
```

The server will start on `http://localhost:8000` with interactive API documentation at `http://localhost:8000/docs`.

## 🏗️ System Architecture

The Onboarder system follows a FastAPI-based architecture with proper state management and context sharing between agents.

### Core Components

1. **FastAPI Server** (`main.py`) - RESTful API endpoints for onboarding management
2. **Agent Orchestrator** - Manages sequential execution of onboarding agents
3. **Context Manager** - Handles onboarding context and markdown templates
4. **Database Manager** - SQLite-based persistent storage with proper state management
5. **Specialized Agents** - Individual agents for different onboarding phases

### Onboarding Phases

1. **Pre-Boarding** - Welcome emails, paperwork, documentation
2. **Day 1 Setup** - IT provisioning, account setup, equipment
3. **Integration** - Scheduling, buddy assignment, training, planning

## 📡 API Endpoints

### Core Endpoints

- `POST /onboarding` - Create new onboarding record
- `GET /onboarding/{employee_id}/status` - Get onboarding status
- `POST /onboarding/{employee_id}/start` - Start onboarding process
- `POST /onboarding/{employee_id}/phase` - Manually update phase status
- `GET /onboarding/{employee_id}/context` - Get onboarding context
- `GET /onboarding/{employee_id}/phase/{phase}/execute` - Execute specific phase
- `GET /onboardings` - List all onboarding records
- `GET /stats` - Get onboarding statistics

### Example Usage

```python
import requests

# Create onboarding record
employee_data = {
    "full_name": "John Doe",
    "personal_email": "john.doe@example.com",
    "job_title": "Software Engineer",
    "manager_name": "Jane Smith",
    "start_date": "2024-01-15",
    "employee_id": "emp_john_doe"
}

response = requests.post("http://localhost:8000/onboarding", json=employee_data)
onboarding = response.json()

# Start onboarding process
employee_id = onboarding["data"]["employee_id"]
response = requests.post(f"http://localhost:8000/onboarding/{employee_id}/start")

# Check status
response = requests.get(f"http://localhost:8000/onboarding/{employee_id}/status")
status = response.json()
```

## 🔄 Workflow

### Sequential Agent Execution

1. **Create Record** - API creates onboarding record with `PENDING` status
2. **Start Process** - API triggers sequential agent execution
3. **Phase Execution** - Agents execute in order: Pre-Boarding → Day 1 Setup → Integration
4. **Context Sharing** - Each agent receives relevant context from markdown templates
5. **State Updates** - Database tracks progress and phase completion
6. **Manual Control** - API allows manual phase updates for demonstration

### Context Management

- **Markdown Templates** - Each phase has a structured markdown template
- **Context Sharing** - Agents receive only relevant information for their phase
- **Progress Tracking** - Templates include checklists and progress indicators
- **Result Integration** - Previous phase results are included in subsequent contexts

## 🛠️ Configuration

### Environment Variables

Create a `.env` file with:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Database

The system uses SQLite with automatic schema initialization. Database file: `onboarding.db`

### Templates

Markdown templates are stored in `onboarder/templates/` and automatically generated for each employee.

## 📊 State Management

### Employee States

- `PENDING` - Onboarding record created, not started
- `IN_PROGRESS` - Onboarding process active
- `COMPLETED` - All phases completed successfully
- `FAILED` - Process failed or encountered errors

### Phase States

- `PRE_BOARDING` - Welcome and paperwork phase
- `DAY1_SETUP` - IT provisioning and setup phase
- `INTEGRATION` - Scheduling, buddy, training, planning phase
- `COMPLETED` - All phases finished

## 🔧 Development

### Project Structure

```
Onboarder/
├── main.py                 # FastAPI server
├── package.json           # npx configuration
├── start_server.sh        # Server startup script
├── requirements.txt       # Python dependencies
├── onboarder/
│   ├── agent_orchestrator.py  # Agent management
│   ├── context_manager.py     # Context and templates
│   ├── database_manager.py    # Database operations
│   ├── templates/             # Markdown templates
│   ├── agents/                # Individual agents
│   └── tools/                 # Utility tools
└── example_api_usage.py   # Usage examples
```

### Running in Development

```bash
# Start with auto-reload
python main.py

# Run example
python example_api_usage.py
```

### Testing

   ```bash
# Quick demo (basic functionality)
python quick_demo.py

# Comprehensive API tests
python test_api_server.py

# Reset database
python reset_database.py

# Lint code
flake8 onboarder/ main.py

# Format code
black onboarder/ main.py
```

## 🌟 Features

### Core Features

- **RESTful API** - Complete REST API for onboarding management
- **Sequential Execution** - Agents run in proper order with dependency management
- **Context Sharing** - Intelligent context sharing between agents
- **State Management** - Proper state tracking and persistence
- **Manual Control** - API endpoints for manual phase management
- **Real-time Status** - Live status updates and progress tracking

### Advanced Features

- **Markdown Templates** - Structured onboarding templates per phase
- **Background Processing** - Async agent execution
- **Error Recovery** - Comprehensive error handling and recovery
- **Statistics** - Onboarding metrics and analytics
- **Documentation** - Auto-generated API documentation
- **npx Support** - Easy installation and usage via npx

## 📈 Monitoring

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### Health Check

```bash
curl http://localhost:8000/health
```

### Statistics

```bash
curl http://localhost:8000/stats
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:

1. Check the API documentation at `/docs`
2. Review the example usage in `example_api_usage.py`
3. Check server logs for detailed error information
4. Ensure your `.env` file is properly configured

## 🔮 Future Enhancements

- Webhook support for external integrations
- Advanced analytics and reporting
- Multi-tenant support
- Integration with HR systems
- Mobile app support
- Advanced workflow customization