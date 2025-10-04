#!/usr/bin/env python3
"""
Comprehensive Test Script for Onboarder FastAPI Server

This script tests all endpoints and functionality of the Onboarder API server.
Run this script while the server is running to validate all features.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 60  # Increased timeout for better performance

# Test Configuration
WAIT_BETWEEN_TESTS = 2  # seconds
WAIT_FOR_AGENTS = 5     # seconds for agent execution

class APITester:
    """Comprehensive API testing class."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.test_results = []
        self.employee_ids = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        if data and not success:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_server_connection(self) -> bool:
        """Test basic server connectivity."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=TIMEOUT)
            success = response.status_code == 200
            self.log_test("Server Connection", success, 
                         f"Status: {response.status_code}" if success else f"Error: {response.text}")
            return success
        except Exception as e:
            self.log_test("Server Connection", False, f"Connection failed: {str(e)}")
            return False
    
    def test_root_endpoint(self) -> bool:
        """Test root endpoint."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=TIMEOUT)
            success = response.status_code == 200
            data = response.json()
            self.log_test("Root Endpoint", success, 
                         f"API Info: {data.get('message', 'Unknown')}" if success else f"Error: {response.text}")
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Request failed: {str(e)}")
            return False
    
    def test_create_onboarding(self, employee_data: Dict[str, str]) -> str:
        """Test creating an onboarding record."""
        try:
            response = requests.post(f"{self.base_url}/onboarding", 
                                   json=employee_data, timeout=TIMEOUT)
            success = response.status_code == 200
            data = response.json()
            
            if success and data.get('success'):
                employee_id = data['data']['employee_id']
                self.employee_ids.append(employee_id)
                self.log_test("Create Onboarding", True, 
                             f"Created employee: {employee_id}")
                return employee_id
            else:
                self.log_test("Create Onboarding", False, 
                             f"Failed: {data.get('message', 'Unknown error')}", data)
                return None
                
        except Exception as e:
            self.log_test("Create Onboarding", False, f"Request failed: {str(e)}")
            return None
    
    def test_get_status(self, employee_id: str) -> bool:
        """Test getting onboarding status."""
        try:
            response = requests.get(f"{self.base_url}/onboarding/{employee_id}/status", 
                                  timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.log_test("Get Status", True, 
                             f"Status: {data.get('status')}, Phase: {data.get('current_phase')}")
                return True
            else:
                self.log_test("Get Status", False, f"Error: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Status", False, f"Request failed: {str(e)}")
            return False
    
    def test_start_onboarding(self, employee_id: str) -> bool:
        """Test starting onboarding process."""
        try:
            response = requests.post(f"{self.base_url}/onboarding/{employee_id}/start", 
                                   timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.log_test("Start Onboarding", True, 
                             f"Started: {data.get('message', 'Unknown')}")
                return True
            else:
                self.log_test("Start Onboarding", False, f"Error: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Start Onboarding", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_context(self, employee_id: str) -> bool:
        """Test getting onboarding context."""
        try:
            response = requests.get(f"{self.base_url}/onboarding/{employee_id}/context", 
                                  timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                context_available = bool(data.get('context'))
                self.log_test("Get Context", True, 
                             f"Context available: {context_available}, Phase: {data.get('current_phase')}")
                return True
            else:
                self.log_test("Get Context", False, f"Error: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Context", False, f"Request failed: {str(e)}")
            return False
    
    def test_update_phase(self, employee_id: str, phase: str, status: str) -> bool:
        """Test manually updating phase status."""
        try:
            data = {"phase": phase, "status": status}
            response = requests.post(f"{self.base_url}/onboarding/{employee_id}/phase", 
                                   json=data, timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                response_data = response.json()
                self.log_test("Update Phase", True, 
                             f"Updated {phase} to {status}")
                return True
            else:
                self.log_test("Update Phase", False, f"Error: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Update Phase", False, f"Request failed: {str(e)}")
            return False
    
    def test_execute_phase(self, employee_id: str, phase: str) -> bool:
        """Test executing a specific phase."""
        try:
            response = requests.get(f"{self.base_url}/onboarding/{employee_id}/phase/{phase}/execute", 
                                  timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.log_test("Execute Phase", True, 
                             f"Executed {phase}: {data.get('message', 'Unknown')}")
                return True
            else:
                self.log_test("Execute Phase", False, f"Error: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Execute Phase", False, f"Request failed: {str(e)}")
            return False
    
    def test_list_onboardings(self, status: str = None) -> bool:
        """Test listing all onboardings."""
        try:
            url = f"{self.base_url}/onboardings"
            if status:
                url += f"?status={status}"
            
            response = requests.get(url, timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                count = data.get('total', 0)
                self.log_test("List Onboardings", True, 
                             f"Found {count} onboarding records")
                return True
            else:
                self.log_test("List Onboardings", False, f"Error: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("List Onboardings", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_stats(self) -> bool:
        """Test getting statistics."""
        try:
            response = requests.get(f"{self.base_url}/stats", timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                total = data.get('total_onboardings', 0)
                self.log_test("Get Stats", True, 
                             f"Total onboardings: {total}")
                return True
            else:
                self.log_test("Get Stats", False, f"Error: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Stats", False, f"Request failed: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling with invalid requests."""
        try:
            # Test invalid employee ID
            response = requests.get(f"{self.base_url}/onboarding/invalid_employee_id/status", 
                                  timeout=TIMEOUT)
            success = response.status_code == 404
            
            if success:
                self.log_test("Error Handling", True, "Properly handles invalid employee ID")
                return True
            else:
                self.log_test("Error Handling", False, f"Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Request failed: {str(e)}")
            return False
    
    def test_validation(self) -> bool:
        """Test input validation."""
        try:
            # Test with missing required fields
            invalid_data = {"full_name": "Test User"}  # Missing required fields
            
            response = requests.post(f"{self.base_url}/onboarding", 
                                   json=invalid_data, timeout=TIMEOUT)
            success = response.status_code == 422  # FastAPI returns 422 for validation errors
            
            if success:
                self.log_test("Input Validation", True, "Properly validates required fields")
                return True
            else:
                self.log_test("Input Validation", False, 
                             f"Expected 422, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Input Validation", False, f"Request failed: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests in sequence."""
        print("🧪 Starting Comprehensive API Tests")
        print("=" * 60)
        
        # Test basic connectivity
        if not self.test_server_connection():
            print("\n❌ Server not accessible. Make sure the server is running on http://localhost:8000")
            return False
        
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Test root endpoint
        self.test_root_endpoint()
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Test validation
        self.test_validation()
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Test error handling
        self.test_error_handling()
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Create test employees
        test_employees = [
            {
                "full_name": "John Doe",
                "personal_email": "john.doe@example.com",
                "job_title": "Software Engineer",
                "manager_name": "Jane Smith",
                "start_date": "2024-01-15"
            },
            {
                "full_name": "Alice Johnson",
                "personal_email": "alice.johnson@example.com",
                "job_title": "Product Manager",
                "manager_name": "Bob Wilson",
                "start_date": "2024-01-20"
            }
        ]
        
        created_employees = []
        
        # Create onboarding records
        for emp_data in test_employees:
            employee_id = self.test_create_onboarding(emp_data)
            if employee_id:
                created_employees.append(employee_id)
            time.sleep(WAIT_BETWEEN_TESTS)
        
        if not created_employees:
            print("\n❌ No employees created. Cannot continue with tests.")
            return False
        
        # Test with first employee
        employee_id = created_employees[0]
        
        # Get initial status
        self.test_get_status(employee_id)
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Get initial context
        self.test_get_context(employee_id)
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Start onboarding process
        self.test_start_onboarding(employee_id)
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Wait for agents to process
        print(f"\n⏳ Waiting {WAIT_FOR_AGENTS} seconds for agents to process...")
        time.sleep(WAIT_FOR_AGENTS)
        
        # Check status after processing
        self.test_get_status(employee_id)
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Get updated context
        self.test_get_context(employee_id)
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Test manual phase update
        self.test_update_phase(employee_id, "PRE_BOARDING", "COMPLETED")
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Test executing specific phase
        self.test_execute_phase(employee_id, "DAY1_SETUP")
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Test listing onboardings
        self.test_list_onboardings()
        time.sleep(WAIT_BETWEEN_TESTS)
        
        self.test_list_onboardings("IN_PROGRESS")
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Test statistics
        self.test_get_stats()
        time.sleep(WAIT_BETWEEN_TESTS)
        
        # Test with second employee (if created)
        if len(created_employees) > 1:
            employee_id_2 = created_employees[1]
            self.test_get_status(employee_id_2)
            time.sleep(WAIT_BETWEEN_TESTS)
            
            self.test_start_onboarding(employee_id_2)
            time.sleep(WAIT_BETWEEN_TESTS)
        
        return True
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['message']}")
        
        print(f"\n👥 Tested Employees: {len(self.employee_ids)}")
        for emp_id in self.employee_ids:
            print(f"   - {emp_id}")
        
        print("\n📝 Test Results JSON:")
        print(json.dumps(self.test_results, indent=2))

def main():
    """Main test function."""
    print("🚀 Onboarder API Server Test Suite")
    print("=" * 60)
    print("This script will test all API endpoints and functionality.")
    print("Make sure the server is running on http://localhost:8000")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server health check failed. Status: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the server first:")
        print("   python main.py")
        sys.exit(1)
    
    # Run tests
    tester = APITester()
    success = tester.run_comprehensive_test()
    
    # Print summary
    tester.print_summary()
    
    if success:
        print("\n🎉 All tests completed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the summary above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
