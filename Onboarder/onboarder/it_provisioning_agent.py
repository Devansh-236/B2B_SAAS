"""
IT Provisioning Agent for the Onboarder system.

Creates user accounts and grants system access for new hires.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

from .tools.llm_utils import LLMUtils, AgentCollaborator

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ITProvisioningAgent:
    """Agent responsible for IT provisioning and system access management."""
    
    def __init__(self, collaborator: AgentCollaborator = None):
        """Initialize the ITProvisioningAgent with Gemini API."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.llm_utils = LLMUtils(self.model)
        self.collaborator = collaborator or AgentCollaborator()
    
    def run(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute the IT provisioning process for a new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            Dict[str, Any]: Status and results of the IT provisioning process
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            personal_email = new_hire_data.get('personal_email', '')
            
            logger.info(f"Starting IT provisioning for {full_name}")
            
            # Generate corporate email
            corporate_email = self._generate_corporate_email(full_name)
            
            # Get insights from other agents
            agent_insights = self.collaborator.get_insights_for_agent('it_provisioning_agent')
            
            # Use structured LLM response to determine system access
            access_schema = {
                "standard_systems": "array",
                "role_specific_systems": "array",
                "department_systems": "array",
                "security_levels": "array",
                "access_timeline": "object"
            }
            
            prompt = f"""
            Determine comprehensive system access for a new employee with this profile:
            - Job Title: {job_title}
            - Department: {new_hire_data.get('department', 'General')}
            - Role Level: {new_hire_data.get('role_level', 'Individual Contributor')}
            
            For each system category, provide:
            - system_name, access_level, justification
            - security_requirements, provisioning_priority
            - estimated_setup_time, dependencies
            
            Consider industry standards, role complexity, and security best practices.
            """
            
            structured_response = self.llm_utils.generate_structured_response(
                prompt, access_schema, agent_insights
            )
            
            if structured_response['success']:
                system_access_data = structured_response['data']
                system_access = system_access_data
                logger.info(f"Generated structured system access requirements for {full_name}")
            else:
                logger.warning(f"Failed to generate structured access requirements: {structured_response['error']}")
                system_access = self._get_fallback_system_access(job_title)
            
            # Provision system access using LLM-driven logic
            access_results = self._provision_system_access_llm(full_name, job_title, system_access)
            
            # Generate temporary password
            temp_password = self._generate_temp_password()
            
            # Create user accounts
            account_results = self._create_user_accounts(full_name, corporate_email, temp_password)
            
            # Share insights with other agents
            self.collaborator.share_insight(
                'it_provisioning_agent',
                'system_access',
                {
                    'access_requirements': system_access,
                    'provisioning_results': access_results,
                    'corporate_email': corporate_email,
                    'security_level': system_access.get('security_levels', [])
                }
            )
            
            # Check if essential systems are provisioned (allow some optional systems to fail)
            essential_systems = ['email_system', 'calendar_system', 'hr_portal', 'vpn_access']
            essential_success = all(access_results.get(system, False) for system in essential_systems)
            status = "SUCCESS" if essential_success and account_results else "FAIL"
            
            result = {
                'status': status,
                'corporate_email': corporate_email,
                'temp_password': temp_password,
                'system_access': system_access,
                'access_results': access_results,
                'account_created': account_results,
                'new_hire_name': full_name
            }
            
            logger.info(f"IT provisioning completed for {full_name} with status: {status}")
            return result
            
        except Exception as e:
            logger.error(f"IT provisioning failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'new_hire_name': new_hire_data.get('full_name', 'Unknown')
            }
    
    def _generate_corporate_email(self, full_name: str) -> str:
        """
        Generate a corporate email address for the new hire.
        
        Args:
            full_name: Full name of the new hire
            
        Returns:
            str: Generated corporate email address
        """
        try:
            # Use Gemini to generate email format
            prompt = f"""
            Generate a professional corporate email address for "{full_name}".
            Use the format: firstname.lastname@company.com
            Handle special characters and spaces appropriately.
            """
            
            response = self.model.generate_content(prompt)
            email_suggestion = response.text.strip()
            
            # Clean up the response to get just the email
            if '@' in email_suggestion:
                corporate_email = email_suggestion.split('\n')[0].strip()
            else:
                # Fallback to simple format
                name_parts = full_name.lower().split()
                if len(name_parts) >= 2:
                    corporate_email = f"{name_parts[0]}.{name_parts[-1]}@company.com"
                else:
                    corporate_email = f"{name_parts[0]}@company.com"
            
            print(f"📧 Generated corporate email: {corporate_email}")
            return corporate_email
            
        except Exception as e:
            logger.error(f"Failed to generate corporate email: {e}")
            # Fallback
            name_parts = full_name.lower().split()
            return f"{name_parts[0]}.{name_parts[-1]}@company.com" if len(name_parts) >= 2 else f"{name_parts[0]}@company.com"
    
    def _provision_system_access(self, full_name: str, job_title: str, system_access: str) -> Dict[str, bool]:
        """
        Provision system access for the new hire.
        
        Args:
            full_name: Full name of the new hire
            job_title: Job title of the new hire
            system_access: System access requirements from Gemini
            
        Returns:
            Dict[str, bool]: Results of access provisioning for each system
        """
        try:
            print(f"🔐 Provisioning system access for {full_name}...")
            print(f"Job title: {job_title}")
            print(f"Access requirements: {system_access}")
            
            # Mock provisioning results
            access_results = {
                'email_system': True,
                'calendar_system': True,
                'hr_portal': True,
                'slack': True,
                'github': job_title.lower() in ['software engineer', 'developer', 'engineer'],
                'salesforce': job_title.lower() in ['sales', 'account manager'],
                'project_management': True,
                'vpn_access': True
            }
            
            for system, success in access_results.items():
                status = "✅" if success else "❌"
                print(f"  {status} {system}: {'Granted' if success else 'Failed'}")
            
            logger.info(f"System access provisioned for {full_name}")
            return access_results
            
        except Exception as e:
            logger.error(f"Failed to provision system access: {e}")
            return {}
    
    def _create_user_accounts(self, full_name: str, corporate_email: str, temp_password: str) -> bool:
        """
        Create user accounts in various systems.
        
        Args:
            full_name: Full name of the new hire
            corporate_email: Corporate email address
            temp_password: Temporary password
            
        Returns:
            bool: True if accounts were created successfully, False otherwise
        """
        try:
            print(f"👤 Creating user accounts for {full_name}...")
            print(f"Email: {corporate_email}")
            print(f"Temp password: {temp_password}")
            
            # Mock account creation
            systems = ['Active Directory', 'Email System', 'HR Portal', 'Slack', 'VPN']
            
            for system in systems:
                print(f"  ✅ {system}: Account created")
            
            logger.info(f"User accounts created for {full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create user accounts: {e}")
            return False
    
    def _generate_temp_password(self) -> str:
        """
        Generate a temporary password for the new hire.
        
        Returns:
            str: Generated temporary password
        """
        import secrets
        import string
        
        # Generate a secure temporary password
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        print(f"🔑 Generated temporary password: {temp_password}")
        return temp_password
    
    def _provision_system_access_llm(self, full_name: str, job_title: str, system_access_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Provision system access using LLM-driven logic.
        
        Args:
            full_name: Full name of the new hire
            job_title: Job title of the new hire
            system_access_data: Structured system access data from LLM
            
        Returns:
            Dict[str, bool]: Results of access provisioning for each system
        """
        try:
            print(f"🔐 Provisioning system access for {full_name} using LLM-driven logic...")
            print(f"Job title: {job_title}")
            
            # Process all system categories
            all_systems = []
            all_systems.extend(system_access_data.get('standard_systems', []))
            all_systems.extend(system_access_data.get('role_specific_systems', []))
            all_systems.extend(system_access_data.get('department_systems', []))
            
            access_results = {}
            
            for system in all_systems:
                system_name = system.get('system_name', 'Unknown')
                access_level = system.get('access_level', 'Standard')
                priority = system.get('provisioning_priority', 'Medium')
                
                # Simulate provisioning based on priority and complexity
                success = self._simulate_system_provisioning(system_name, access_level, priority)
                access_results[system_name.lower().replace(' ', '_')] = success
                
                status = "✅" if success else "❌"
                print(f"  {status} {system_name} ({access_level} access) - Priority: {priority}")
            
            # Add standard systems if not already included
            standard_systems = {
                'email_system': True,
                'calendar_system': True,
                'hr_portal': True,
                'vpn_access': True
            }
            
            for system, default_success in standard_systems.items():
                if system not in access_results:
                    access_results[system] = default_success
                    status = "✅" if default_success else "❌"
                    print(f"  {status} {system}: Standard provisioning")
            
            logger.info(f"LLM-driven system access provisioned for {full_name}")
            return access_results
            
        except Exception as e:
            logger.error(f"Failed to provision system access using LLM: {e}")
            return self._provision_system_access(full_name, job_title, str(system_access_data))
    
    def _simulate_system_provisioning(self, system_name: str, access_level: str, priority: str) -> bool:
        """
        Simulate system provisioning based on system requirements.
        
        Args:
            system_name: Name of the system
            access_level: Required access level
            priority: Provisioning priority
            
        Returns:
            bool: True if provisioning succeeded, False otherwise
        """
        # Simulate different success rates based on priority and complexity
        success_rates = {
            'High': 0.95,
            'Medium': 0.90,
            'Low': 0.85
        }
        
        # Adjust success rate based on access level complexity
        complexity_modifiers = {
            'Admin': 0.8,
            'Standard': 1.0,
            'Read-Only': 1.1,
            'Basic': 1.1
        }
        
        base_rate = success_rates.get(priority, 0.90)
        modifier = complexity_modifiers.get(access_level, 1.0)
        final_rate = min(base_rate * modifier, 0.99)  # Cap at 99%
        
        import random
        return random.random() < final_rate
    
    def _get_fallback_system_access(self, job_title: str) -> Dict[str, Any]:
        """
        Get fallback system access when LLM generation fails.
        
        Args:
            job_title: Job title of the new hire
            
        Returns:
            Dict[str, Any]: Basic system access requirements
        """
        return {
            "standard_systems": [
                {
                    "system_name": "Email System",
                    "access_level": "Standard",
                    "provisioning_priority": "High"
                },
                {
                    "system_name": "Calendar System", 
                    "access_level": "Standard",
                    "provisioning_priority": "High"
                }
            ],
            "role_specific_systems": [],
            "department_systems": [],
            "security_levels": ["Standard"],
            "access_timeline": {"estimated_days": 1}
        }
