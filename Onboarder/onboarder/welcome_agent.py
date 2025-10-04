"""
Welcome Agent for the Onboarder system.

Handles welcome email and kit logistics for new hires.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

from .tools.email_sender import EmailSender

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class WelcomeAgent:
    """Agent responsible for welcoming new hires and managing welcome kit logistics."""
    
    def __init__(self):
        """Initialize the WelcomeAgent with Gemini API."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.email_sender = EmailSender()
    
    def run(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute the welcome process for a new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            Dict[str, Any]: Status and results of the welcome process
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            logger.info(f"Starting welcome process for {full_name}")
            
            # Use Gemini to generate personalized welcome message
            prompt = f"""
            Generate a personalized welcome message for a new employee with the following details:
            - Name: {full_name}
            - Job Title: {new_hire_data.get('job_title', 'Employee')}
            - Start Date: {new_hire_data.get('start_date', 'TBD')}
            - Manager: {new_hire_data.get('manager_name', 'Manager')}
            
            The message should be warm, professional, and include:
            1. A personal welcome
            2. Information about what to expect on their first day
            3. Mention of the welcome kit being sent
            4. Encouragement to reach out with questions
            
            Keep it concise but friendly.
            """
            
            response = self.model.generate_content(prompt)
            welcome_message = response.text
            
            # Send welcome email
            email_success = self.email_sender.send_welcome_email(new_hire_data)
            
            # Log welcome kit request
            kit_success = self._request_welcome_kit(new_hire_data)
            
            status = "SUCCESS" if email_success and kit_success else "FAIL"
            
            result = {
                'status': status,
                'welcome_message': welcome_message,
                'email_sent': email_success,
                'welcome_kit_requested': kit_success,
                'new_hire_name': full_name
            }
            
            logger.info(f"Welcome process completed for {full_name} with status: {status}")
            return result
            
        except Exception as e:
            logger.error(f"Welcome process failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'new_hire_name': new_hire_data.get('full_name', 'Unknown')
            }
    
    def _request_welcome_kit(self, new_hire_data: Dict[str, str]) -> bool:
        """
        Request a welcome kit to be shipped to the new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            bool: True if request was successful, False otherwise
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            personal_email = new_hire_data.get('personal_email', '')
            
            # Use Gemini to generate kit contents based on role
            prompt = f"""
            Based on the job title "{new_hire_data.get('job_title', 'Employee')}", 
            suggest appropriate welcome kit contents for a new employee. 
            Include company swag, office supplies, and role-specific items.
            Format as a simple list.
            """
            
            response = self.model.generate_content(prompt)
            kit_contents = response.text
            
            print(f"🎁 Requesting welcome kit for {full_name}...")
            print(f"Email: {personal_email}")
            print(f"Kit contents: {kit_contents}")
            
            # In a real implementation, you would integrate with a shipping/logistics system
            logger.info(f"Welcome kit requested for {full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to request welcome kit: {e}")
            return False
