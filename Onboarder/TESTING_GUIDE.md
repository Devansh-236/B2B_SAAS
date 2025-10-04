# Testing Guide for Onboarder API Server

## 🎯 Overview

This guide provides comprehensive testing instructions for the Onboarder FastAPI server with automatic employee ID generation and proper database management.

## ✅ Completed Updates

### 1. Database Reset
- ✅ Cleared existing database
- ✅ Updated schema with proper employee ID handling
- ✅ Added automatic employee ID generation
- ✅ Added database reset functionality

### 2. Automatic Employee ID Generation
- ✅ Employee IDs are now auto-generated when not provided
- ✅ Format: `emp_{name_clean}_{timestamp}`
- ✅ Special characters are cleaned from names
- ✅ Timestamps ensure uniqueness

### 3. Test Scripts Created
- ✅ `test_api_server.py` - Comprehensive API testing
- ✅ `quick_demo.py` - Simple demonstration script
- ✅ `reset_database.py` - Database reset utility

## 🚀 Quick Start Testing

### 1. Start the Server
```bash
# Option 1: Using the startup script
./start_server.sh

# Option 2: Direct Python
python main.py

# Option 3: Using npx (if published)
npx onboarder-api
```

### 2. Run Quick Demo
```bash
python quick_demo.py
```

This will:
- Check server connectivity
- Create a test employee (with auto-generated ID)
- Start onboarding process
- Show status updates
- Display statistics

### 3. Run Comprehensive Tests
```bash
python test_api_server.py
```

This will test:
- All API endpoints
- Error handling
- Input validation
- Multiple employee creation
- Phase management
- Context retrieval
- Statistics

## 📊 Test Scripts Overview

### `quick_demo.py`
- **Purpose**: Simple demonstration of basic API functionality
- **Duration**: ~30 seconds
- **Tests**: Basic CRUD operations, status checking
- **Use Case**: Quick verification that server is working

### `test_api_server.py`
- **Purpose**: Comprehensive testing of all API endpoints
- **Duration**: ~2-3 minutes
- **Tests**: All endpoints, error handling, validation, edge cases
- **Use Case**: Full regression testing, CI/CD integration

### `reset_database.py`
- **Purpose**: Clear database and reinitialize schema
- **Duration**: ~5 seconds
- **Use Case**: Fresh start, testing cleanup

## 🔧 API Testing Examples

### Create Employee (Auto ID)
```python
import requests

employee_data = {
    "full_name": "John Doe",
    "personal_email": "john.doe@example.com",
    "job_title": "Software Engineer",
    "manager_name": "Jane Smith",
    "start_date": "2024-01-15"
    # employee_id is optional - will be auto-generated
}

response = requests.post("http://localhost:8000/onboarding", json=employee_data)
result = response.json()
employee_id = result["data"]["employee_id"]  # Auto-generated ID
```

### Check Status
```python
response = requests.get(f"http://localhost:8000/onboarding/{employee_id}/status")
status = response.json()
print(f"Status: {status['status']}, Phase: {status['current_phase']}")
```

### Start Onboarding
```python
response = requests.post(f"http://localhost:8000/onboarding/{employee_id}/start")
print("Onboarding started!")
```

## 📈 Expected Test Results

### Quick Demo Expected Output
```
🚀 Onboarder API Quick Demo
✅ Server is running!
📝 Creating onboarding for: Demo Employee
✅ Created employee: emp_demo_employee_20241204_143022
📊 Getting status for: emp_demo_employee_20241204_143022
✅ Status: PENDING, Phase: PRE_BOARDING
🚀 Starting onboarding for: emp_demo_employee_20241204_143022
✅ Started: Onboarding process started
⏳ Waiting 3 seconds for processing...
📊 Checking updated status...
✅ Updated Status: IN_PROGRESS, Phase: PRE_BOARDING
📋 Getting onboarding context...
✅ Context available for phase: PRE_BOARDING
📝 Getting all onboarding records...
✅ Found 1 onboarding records
📈 Getting statistics...
✅ Statistics: Total onboardings: 1
🎉 Demo completed!
```

### Comprehensive Test Expected Output
```
🧪 Starting Comprehensive API Tests
✅ PASS Server Connection
✅ PASS Root Endpoint
✅ PASS Input Validation
✅ PASS Error Handling
✅ PASS Create Onboarding
✅ PASS Get Status
✅ PASS Start Onboarding
✅ PASS Get Context
✅ PASS Update Phase
✅ PASS Execute Phase
✅ PASS List Onboardings
✅ PASS Get Stats

📊 TEST SUMMARY
Total Tests: 12
✅ Passed: 12
❌ Failed: 0
Success Rate: 100.0%
```

## 🗄️ Database Management

### Reset Database
```bash
python reset_database.py
```

### Manual Database Operations
```python
from onboarder.database_manager import DatabaseManager

db = DatabaseManager()

# Clear all data
db.clear_database()

# Reset completely
db.reset_database()

# Get all records
records = db.get_all_onboarding_records()

# Get by employee ID
record = db.get_onboarding_by_employee_id("emp_john_doe_20241204_143022")
```

## 🔍 Troubleshooting

### Server Not Starting
```bash
# Check if port 8000 is in use
lsof -i :8000

# Check Python dependencies
pip install -r requirements.txt

# Check environment variables
cat .env
```

### Database Issues
```bash
# Reset database
python reset_database.py

# Check database file
ls -la onboarding.db

# Remove and recreate
rm onboarding.db
python -c "from onboarder.database_manager import DatabaseManager; DatabaseManager()"
```

### API Connection Issues
```bash
# Test server health
curl http://localhost:8000/health

# Test root endpoint
curl http://localhost:8000/

# Check server logs
python main.py  # Run in foreground to see logs
```

## 📝 Test Data Examples

### Sample Employee Data
```python
employees = [
    {
        "full_name": "Alice Johnson",
        "personal_email": "alice.johnson@company.com",
        "job_title": "Software Engineer",
        "manager_name": "Bob Smith",
        "start_date": "2024-01-15"
    },
    {
        "full_name": "Charlie Brown",
        "personal_email": "charlie.brown@company.com",
        "job_title": "Product Manager",
        "manager_name": "Diana Prince",
        "start_date": "2024-01-20"
    },
    {
        "full_name": "Eve Wilson",
        "personal_email": "eve.wilson@company.com",
        "job_title": "UX Designer",
        "manager_name": "Frank Miller",
        "start_date": "2024-01-25"
    }
]
```

## 🎉 Success Criteria

Your system is working correctly if:

1. ✅ Server starts without errors
2. ✅ Database initializes properly
3. ✅ Employee IDs are auto-generated
4. ✅ All API endpoints respond correctly
5. ✅ Onboarding process can be started and tracked
6. ✅ Context is properly shared between phases
7. ✅ Statistics are accurate
8. ✅ Error handling works properly

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🚀 Next Steps

After successful testing:

1. Deploy to production environment
2. Set up monitoring and logging
3. Configure webhook integrations
4. Add authentication/authorization
5. Set up CI/CD pipeline with automated testing
