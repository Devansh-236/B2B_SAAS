"""
Document Generator utility for the Onboarder system.

Provides functionality to generate onboarding documents from templates.
Documents are currently written as plain-text placeholders (.txt), not PDFs.
"""

import os
import re
import uuid
from typing import Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Onboarder project directory (parent of the onboarder package)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _default_output_dir() -> str:
    """Resolve the output directory from DOCUMENT_OUTPUT_DIR, relative to the project directory."""
    output_dir = os.getenv('DOCUMENT_OUTPUT_DIR', 'generated_documents')
    return os.path.join(PROJECT_DIR, output_dir)


class DocumentGenerator:
    """Utility class for generating documents from templates."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the DocumentGenerator.
        
        Args:
            output_dir: Directory to save generated documents. Defaults to
                DOCUMENT_OUTPUT_DIR (or "generated_documents") inside the project directory.
        """
        self.output_dir = os.path.realpath(output_dir or _default_output_dir())
        os.makedirs(self.output_dir, exist_ok=True)
    
    @staticmethod
    def _slugify(value: str, max_length: int = 64) -> str:
        """Reduce a value to a filename-safe slug containing only [a-z0-9_-]."""
        slug = re.sub(r'[^a-z0-9_-]+', '_', str(value).lower()).strip('_-')
        return slug[:max_length]
    
    def _build_filepath(self, prefix: str, new_hire_data: Dict[str, str]) -> str:
        """
        Build a safe, unique path inside output_dir for a generated document.
        
        Args:
            prefix: Document type prefix (e.g. "employment_contract")
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            str: Absolute path of the file to write
        """
        safe_name = self._slugify(new_hire_data.get('full_name') or 'new_hire', 50) or 'new_hire'
        unique_id = self._slugify(new_hire_data.get('employee_id') or '') or uuid.uuid4().hex[:8]
        filename = f"{prefix}_{safe_name}_{unique_id}_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath = os.path.realpath(os.path.join(self.output_dir, filename))
        
        # Never write outside the output directory
        if os.path.dirname(filepath) != self.output_dir:
            raise ValueError(f"Refusing to write outside output directory: {filepath}")
        
        return filepath
    
    def generate_employment_contract(self, new_hire_data: Dict[str, str]) -> str:
        """
        Generate an employment contract (plain-text placeholder) for the new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            str: Path to the generated contract file
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            start_date = new_hire_data.get('start_date', 'TBD')
            manager_name = new_hire_data.get('manager_name', 'Manager')
            
            # Generate filename
            filepath = self._build_filepath("employment_contract", new_hire_data)
            
            # Generate contract content
            contract_content = f"""
            EMPLOYMENT CONTRACT
            
            Employee: {full_name}
            Position: {job_title}
            Start Date: {start_date}
            Manager: {manager_name}
            
            TERMS AND CONDITIONS:
            
            1. POSITION AND DUTIES
            The Employee agrees to serve as {job_title} and to perform such duties
            as may be assigned by the Company.
            
            2. COMPENSATION
            The Employee will receive compensation as agreed upon in the offer letter.
            
            3. BENEFITS
            The Employee will be eligible for company benefits as outlined in the
            employee handbook.
            
            4. CONFIDENTIALITY
            The Employee agrees to maintain confidentiality of all company information.
            
            5. TERMINATION
            Either party may terminate this agreement with appropriate notice.
            
            This contract is effective as of {start_date}.
            
            Employee Signature: _________________ Date: _________
            Manager Signature: _________________ Date: _________
            """
            
            print(f"📄 Generating employment contract for {full_name}...")
            print(f"File: {filepath}")
            print(f"Content preview: {contract_content[:200]}...")
            
            # In a real implementation, you would generate an actual PDF here
            # For now, we'll create a text file as a placeholder
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(contract_content)
            
            logger.info(f"Employment contract generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate employment contract: {e}")
            return ""
    
    def generate_personal_info_form(self, new_hire_data: Dict[str, str]) -> str:
        """
        Generate a personal information collection form.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            str: Path to the generated form file
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            
            # Generate filename
            filepath = self._build_filepath("personal_info_form", new_hire_data)
            
            # Generate form content
            form_content = f"""
            PERSONAL INFORMATION FORM
            
            Employee: {full_name}
            
            Please provide the following information:
            
            1. Full Legal Name: _________________________
            2. Preferred Name: _________________________
            3. Date of Birth: _________________________
            4. Social Security Number: _________________________
            5. Address: _________________________
            6. Phone Number: _________________________
            7. Emergency Contact Name: _________________________
            8. Emergency Contact Phone: _________________________
            9. Emergency Contact Relationship: _________________________
            10. Bank Account Information (for direct deposit):
                Bank Name: _________________________
                Account Number: _________________________
                Routing Number: _________________________
            
            11. Tax Information:
                Marital Status: _________________________
                Number of Dependents: _________________________
            
            12. Emergency Medical Information:
                Allergies: _________________________
                Medical Conditions: _________________________
                Current Medications: _________________________
            
            Signature: _________________________ Date: _________
            """
            
            print(f"📄 Generating personal info form for {full_name}...")
            print(f"File: {filepath}")
            print(f"Content preview: {form_content[:200]}...")
            
            # In a real implementation, you would generate an actual PDF here
            # For now, we'll create a text file as a placeholder
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(form_content)
            
            logger.info(f"Personal info form generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate personal info form: {e}")
            return ""
    
    def generate_integration_plan(self, new_hire_data: Dict[str, str], plan_data: Dict) -> str:
        """
        Generate a 30-60-90 day integration plan document.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            plan_data: Dictionary containing the integration plan details
            
        Returns:
            str: Path to the generated plan file
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            
            # Generate filename
            filepath = self._build_filepath("integration_plan", new_hire_data)
            
            # Generate plan content
            plan_content = f"""
            30-60-90 DAY INTEGRATION PLAN
            
            Employee: {full_name}
            Position: {job_title}
            Start Date: {new_hire_data.get('start_date', 'TBD')}
            
            FIRST 30 DAYS - LEARNING & ORIENTATION
            {plan_data.get('30_days', 'Complete company orientation and training')}
            
            DAYS 31-60 - CONTRIBUTION & COLLABORATION
            {plan_data.get('60_days', 'Begin contributing to team projects')}
            
            DAYS 61-90 - INDEPENDENCE & LEADERSHIP
            {plan_data.get('90_days', 'Take on independent projects and mentor others')}
            
            KEY MILESTONES:
            {plan_data.get('milestones', 'Complete all mandatory training')}
            
            SUCCESS METRICS:
            {plan_data.get('metrics', 'Meet with manager weekly for feedback')}
            
            Manager: {new_hire_data.get('manager_name', 'Manager')}
            """
            
            print(f"📄 Generating integration plan for {full_name}...")
            print(f"File: {filepath}")
            print(f"Content preview: {plan_content[:200]}...")
            
            # In a real implementation, you would generate an actual PDF here
            # For now, we'll create a text file as a placeholder
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(plan_content)
            
            logger.info(f"Integration plan generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate integration plan: {e}")
            return ""
