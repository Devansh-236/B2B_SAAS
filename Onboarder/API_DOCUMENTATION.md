# Onboarder API Documentation

## Overview

The Onboarder API is a RESTful service for managing employee onboarding processes. It provides endpoints to create, monitor, and control onboarding workflows with intelligent agent-based automation.

**Base URL:** `http://localhost:8050`  
**API Version:** 1.0.0  
**Documentation:** `http://localhost:8050/docs` (Swagger UI)  
**Alternative Docs:** `http://localhost:8050/redoc` (ReDoc)

## Timeout Settings & Performance Guidelines

### Recommended Timeout Settings

When using the API in automation scripts, configure the following timeout values:

```python
# Recommended timeout settings for automation
REQUEST_TIMEOUT = 30  # seconds for most endpoints
HEALTH_CHECK_TIMEOUT = 5  # seconds for health checks
BACKGROUND_PROCESS_WAIT = 60  # seconds for onboarding completion
POLLING_INTERVAL = 5  # seconds between status checks
```

### Timeout Considerations

1. **Standard Endpoints (5-30 seconds):**
   - Health checks: 5 seconds
   - CRUD operations: 15-30 seconds
   - Status retrieval: 10-15 seconds

2. **Background Process Endpoints (30-90 seconds):**
   - Starting onboarding: 30-60 seconds
   - Phase execution: 30-60 seconds
   - Agent processing: 60-90 seconds

3. **Polling Strategy:**
   - Check status every 5-10 seconds
   - Maximum wait time: 5-10 minutes for full onboarding
   - Implement exponential backoff for retries

### Error Handling & Retries

```python
# Recommended retry strategy
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
EXPONENTIAL_BACKOFF = True
```

## Authentication

Currently, the API runs without authentication. In production environments, implement appropriate authentication mechanisms.

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API server is running and healthy.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00"
}
```

**Timeout:** 5 seconds

---

### 2. API Information

**GET** `/`

Get basic API information and available endpoints.

**Response:**
```json
{
  "message": "Onboarder API Server",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "create_onboarding": "/onboarding",
    "get_status": "/onboarding/{employee_id}/status",
    "start_onboarding": "/onboarding/{employee_id}/start",
    "update_phase": "/onboarding/{employee_id}/phase",
    "get_context": "/onboarding/{employee_id}/context",
    "list_onboardings": "/onboardings"
  }
}
```

**Timeout:** 5 seconds

---

### 3. Create Onboarding Record

**POST** `/onboarding`

Create a new onboarding record for an employee. This endpoint only creates the record but doesn't start the process.

**Request Body:**
```json
{
  "full_name": "John Doe",
  "personal_email": "john.doe@example.com",
  "job_title": "Software Engineer",
  "manager_name": "Jane Smith",
  "start_date": "2024-01-15",
  "employee_id": "EMP001"  // Optional, auto-generated if not provided
}
```

**Field Requirements:**
- `full_name`: Required, string
- `personal_email`: Required, valid email format
- `job_title`: Required, string
- `manager_name`: Required, string
- `start_date`: Required, format YYYY-MM-DD
- `employee_id`: Optional, string (auto-generated if not provided)

**Response:**
```json
{
  "success": true,
  "message": "Onboarding record created successfully",
  "data": {
    "employee_id": "EMP001",
    "onboarding_id": "onb_123456",
    "status": "PENDING",
    "current_phase": "PRE_BOARDING"
  }
}
```

**Timeout:** 15 seconds

**Status Codes:**
- `200`: Success
- `400`: Bad request (validation error)
- `422`: Validation error (invalid data format)
- `500`: Internal server error

---

### 4. Get Onboarding Status

**GET** `/onboarding/{employee_id}/status`

Retrieve the current status of an employee's onboarding process.

**Path Parameters:**
- `employee_id`: The employee's unique identifier

**Response:**
```json
{
  "employee_id": "EMP001",
  "status": "IN_PROGRESS",
  "current_phase": "DAY1_SETUP",
  "completed_phases": ["PRE_BOARDING"],
  "start_time": "2024-01-15T10:30:00",
  "last_updated": "2024-01-15T11:15:00",
  "process_log": [
    "Onboarding process started",
    "PRE_BOARDING phase completed",
    "DAY1_SETUP phase started"
  ]
}
```

**Status Values:**
- `PENDING`: Record created but not started
- `IN_PROGRESS`: Onboarding is actively running
- `COMPLETED`: All phases completed successfully
- `FAILED`: Process encountered an error

**Phase Values:**
- `PRE_BOARDING`: Initial setup and paperwork
- `DAY1_SETUP`: First day preparations
- `INTEGRATION`: Team integration and training

**Timeout:** 10 seconds

**Status Codes:**
- `200`: Success
- `404`: Employee not found
- `500`: Internal server error

---

### 5. Start Onboarding Process

**POST** `/onboarding/{employee_id}/start`

Start the onboarding process for an employee. This triggers the background agent workflow.

**Path Parameters:**
- `employee_id`: The employee's unique identifier

**Response:**
```json
{
  "success": true,
  "message": "Onboarding process started",
  "data": {
    "employee_id": "EMP001",
    "onboarding_id": "onb_123456",
    "current_phase": "PRE_BOARDING",
    "status": "IN_PROGRESS"
  }
}
```

**Important Notes:**
- This is a background process that may take several minutes
- Use the status endpoint to monitor progress
- The process runs asynchronously with error handling

**Timeout:** 30-60 seconds (may take longer for initial setup)

**Status Codes:**
- `200`: Process started successfully
- `400`: Bad request (already in progress/completed)
- `404`: Employee not found
- `500`: Internal server error

---

### 6. Update Phase Status

**POST** `/onboarding/{employee_id}/phase`

Manually update the status of a specific onboarding phase.

**Path Parameters:**
- `employee_id`: The employee's unique identifier

**Request Body:**
```json
{
  "phase": "PRE_BOARDING",
  "status": "COMPLETED"
}
```

**Valid Phase Values:**
- `PRE_BOARDING`
- `DAY1_SETUP`
- `INTEGRATION`

**Valid Status Values:**
- `PENDING`: Phase not started
- `IN_PROGRESS`: Phase currently running
- `COMPLETED`: Phase finished successfully
- `FAILED`: Phase encountered an error

**Response:**
```json
{
  "success": true,
  "message": "Phase PRE_BOARDING updated to COMPLETED",
  "data": {
    "employee_id": "EMP001",
    "current_phase": "DAY1_SETUP",
    "completed_phases": ["PRE_BOARDING"]
  }
}
```

**Timeout:** 15 seconds

**Status Codes:**
- `200`: Success
- `400`: Invalid phase or status
- `404`: Employee not found
- `500`: Internal server error

---

### 7. Execute Specific Phase

**GET** `/onboarding/{employee_id}/phase/{phase}/execute`

Trigger the execution of a specific onboarding phase.

**Path Parameters:**
- `employee_id`: The employee's unique identifier
- `phase`: The phase to execute (`PRE_BOARDING`, `DAY1_SETUP`, `INTEGRATION`)

**Response:**
```json
{
  "success": true,
  "message": "Phase PRE_BOARDING execution started",
  "data": {
    "employee_id": "EMP001",
    "phase": "PRE_BOARDING",
    "status": "EXECUTING"
  }
}
```

**Timeout:** 30-60 seconds (depends on phase complexity)

**Status Codes:**
- `200`: Phase execution started
- `404`: Employee not found
- `500`: Internal server error

---

### 8. Get Onboarding Context

**GET** `/onboarding/{employee_id}/context`

Retrieve the onboarding context and templates for an employee's current phase.

**Path Parameters:**
- `employee_id`: The employee's unique identifier

**Response:**
```json
{
  "employee_id": "EMP001",
  "current_phase": "PRE_BOARDING",
  "context": {
    "templates": ["welcome_email", "equipment_list"],
    "checklist": ["paperwork", "account_setup"],
    "next_steps": ["manager_introduction", "team_meeting"]
  },
  "all_context": {
    "PRE_BOARDING": {...},
    "DAY1_SETUP": {...},
    "INTEGRATION": {...}
  }
}
```

**Timeout:** 15 seconds

**Status Codes:**
- `200`: Success
- `404`: Employee not found
- `500`: Internal server error

---

### 9. List All Onboardings

**GET** `/onboardings`

Retrieve a list of all onboarding records, optionally filtered by status.

**Query Parameters:**
- `status`: Optional filter (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`)

**Example:** `GET /onboardings?status=IN_PROGRESS`

**Response:**
```json
{
  "total": 5,
  "onboardings": [
    {
      "employee_id": "EMP001",
      "onboarding_id": "onb_123456",
      "status": "IN_PROGRESS",
      "current_phase": "DAY1_SETUP",
      "start_time": "2024-01-15T10:30:00",
      "last_updated": "2024-01-15T11:15:00",
      "new_hire_data": {
        "full_name": "John Doe",
        "job_title": "Software Engineer"
      }
    }
  ]
}
```

**Timeout:** 15 seconds

**Status Codes:**
- `200`: Success
- `500`: Internal server error

---

### 10. Get Statistics

**GET** `/stats`

Retrieve summary statistics for all onboarding processes.

**Response:**
```json
{
  "total_onboardings": 25,
  "by_status": {
    "PENDING": 5,
    "IN_PROGRESS": 8,
    "COMPLETED": 10,
    "FAILED": 2
  },
  "by_phase": {
    "PRE_BOARDING": 3,
    "DAY1_SETUP": 4,
    "INTEGRATION": 1
  },
  "average_completion_time": "2.5 days",
  "success_rate": "83.3%"
}
```

**Timeout:** 15 seconds

**Status Codes:**
- `200`: Success
- `500`: Internal server error

## Python Automation Example

Here's a complete Python script example for using the API in automation:

```python
import requests
import time
import json
from typing import Dict, Any, Optional

class OnboarderAPI:
    """Python client for Onboarder API."""
    
    def __init__(self, base_url: str = "http://localhost:8050"):
        self.base_url = base_url
        self.timeout = 30
        self.health_timeout = 5
        self.polling_interval = 5
        self.max_wait_time = 600  # 10 minutes
    
    def health_check(self) -> bool:
        """Check if the API server is healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.health_timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def create_onboarding(self, employee_data: Dict[str, str]) -> Optional[str]:
        """Create a new onboarding record."""
        try:
            response = requests.post(
                f"{self.base_url}/onboarding",
                json=employee_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                return data['data']['employee_id']
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error creating onboarding: {e}")
            return None
    
    def start_onboarding(self, employee_id: str) -> bool:
        """Start the onboarding process."""
        try:
            response = requests.post(
                f"{self.base_url}/onboarding/{employee_id}/start",
                timeout=60  # Longer timeout for background processes
            )
            response.raise_for_status()
            data = response.json()
            return data.get('success', False)
        except requests.exceptions.RequestException as e:
            print(f"Error starting onboarding: {e}")
            return False
    
    def get_status(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding status."""
        try:
            response = requests.get(
                f"{self.base_url}/onboarding/{employee_id}/status",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting status: {e}")
            return None
    
    def wait_for_completion(self, employee_id: str, max_wait: int = None) -> bool:
        """Wait for onboarding to complete with polling."""
        if max_wait is None:
            max_wait = self.max_wait_time
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = self.get_status(employee_id)
            if not status:
                time.sleep(self.polling_interval)
                continue
            
            current_status = status.get('status')
            print(f"Status: {current_status}, Phase: {status.get('current_phase')}")
            
            if current_status == 'COMPLETED':
                return True
            elif current_status == 'FAILED':
                print(f"Onboarding failed: {status.get('process_log', [])}")
                return False
            
            time.sleep(self.polling_interval)
        
        print(f"Timeout reached after {max_wait} seconds")
        return False
    
    def get_context(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding context."""
        try:
            response = requests.get(
                f"{self.base_url}/onboarding/{employee_id}/context",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting context: {e}")
            return None
    
    def list_onboardings(self, status: str = None) -> Optional[Dict[str, Any]]:
        """List all onboardings."""
        try:
            url = f"{self.base_url}/onboardings"
            if status:
                url += f"?status={status}"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error listing onboardings: {e}")
            return None
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get API statistics."""
        try:
            response = requests.get(f"{self.base_url}/stats", timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting stats: {e}")
            return None

# Example usage
def main():
    """Example automation script."""
    api = OnboarderAPI()
    
    # Check if server is running
    if not api.health_check():
        print("❌ API server is not running. Please start it first.")
        return
    
    print("✅ API server is healthy")
    
    # Create onboarding record
    employee_data = {
        "full_name": "Jane Smith",
        "personal_email": "jane.smith@example.com",
        "job_title": "Product Manager",
        "manager_name": "John Doe",
        "start_date": "2024-01-20"
    }
    
    employee_id = api.create_onboarding(employee_data)
    if not employee_id:
        print("❌ Failed to create onboarding record")
        return
    
    print(f"✅ Created onboarding for employee: {employee_id}")
    
    # Start onboarding process
    if not api.start_onboarding(employee_id):
        print("❌ Failed to start onboarding process")
        return
    
    print("✅ Started onboarding process")
    
    # Wait for completion
    print("⏳ Waiting for onboarding to complete...")
    if api.wait_for_completion(employee_id, max_wait=300):  # 5 minutes max
        print("🎉 Onboarding completed successfully!")
        
        # Get final status
        status = api.get_status(employee_id)
        if status:
            print(f"Final status: {status['status']}")
            print(f"Completed phases: {status['completed_phases']}")
    else:
        print("⏰ Onboarding did not complete within the timeout period")
    
    # Get statistics
    stats = api.get_stats()
    if stats:
        print(f"\n📊 API Statistics:")
        print(f"Total onboardings: {stats.get('total_onboardings', 0)}")
        print(f"Success rate: {stats.get('success_rate', 'N/A')}")

if __name__ == "__main__":
    main()
```

## Error Handling

### Common HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Retry Strategy

For automation scripts, implement exponential backoff:

```python
import time
import random

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
```

## Best Practices

### 1. Timeout Configuration
- Use appropriate timeouts for different endpoint types
- Implement graceful timeout handling
- Consider background process completion times

### 2. Polling Strategy
- Poll status endpoints every 10-30 seconds
- Implement maximum wait times
- Use exponential backoff for retries

### 3. Error Handling
- Always check HTTP status codes
- Implement retry logic for transient failures
- Log errors for debugging

### 4. Performance Optimization
- Cache frequently accessed data
- Use concurrent requests when appropriate
- Monitor API response times

### 5. Security Considerations
- Validate input data before sending
- Implement rate limiting in automation scripts
- Use HTTPS in production environments

## Monitoring and Debugging

### Health Monitoring
```python
# Regular health checks
def monitor_api_health():
    if not api.health_check():
        # Send alert or log error
        pass
```

### Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log API calls
logger.info(f"Starting onboarding for employee: {employee_id}")
```

### Metrics Collection
```python
import time

def track_api_performance():
    start_time = time.time()
    # Make API call
    response_time = time.time() - start_time
    # Log or send to metrics system
```

This documentation provides comprehensive information for using the Onboarder API in automation scripts with proper timeout handling and error management.
