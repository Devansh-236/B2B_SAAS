"""
Paperwork Agent for the Onboarder system.

Manages contracts, forms, and data collection for new hires.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

from .tools.document_generator import DocumentGenerator
from .tools.email_sender import EmailSender
from .tools.llm_utils import LLM_REQUEST_OPTIONS

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PaperworkAgent:
    """Agent responsible for managing employment paperwork and documentation."""
    
    def __init__(self):
        """Initialize the PaperworkAgent with Gemini API."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.document_generator = DocumentGenerator()
        self.email_sender = EmailSender()
    
    def run(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute the paperwork process for a new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            Dict[str, Any]: Status and results of the paperwork process
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            logger.info(f"Starting paperwork process for {full_name}")
            
            # Generate employment contract
            contract_path = self.document_generator.generate_employment_contract(new_hire_data)
            
            # Generate personal info form
            form_path = self.document_generator.generate_personal_info_form(new_hire_data)
            
            # Send contract for e-signature
            contract_email_sent = self.email_sender.send_contract_email(new_hire_data, contract_path)
            
            # Use Gemini to generate personalized form instructions
            prompt = f"""
            Generate clear instructions for a new employee named {full_name} 
            about completing their personal information form. Include:
            1. Why the form is needed
            2. What information is required
            3. How to submit the form
            4. Timeline for completion
            5. Who to contact with questions
            
            Keep it professional and helpful.
            """
            
            response = self.model.generate_content(prompt, request_options=LLM_REQUEST_OPTIONS)
            form_instructions = response.text
            
            # Mock e-signature process
            signature_status = self._process_e_signature(new_hire_data, contract_path)
            
            if not contract_path or not form_path:
                # Document generation failed; nothing valid to sign or fill in
                status = "FAIL"
            elif signature_status == "completed":
                status = "COMPLETED"
            elif signature_status == "pending":
                status = "AWAITING_SIGNATURE"
            else:
                status = "FAIL"

            result = {
                'status': status,
                'contract_generated': bool(contract_path),
                'form_generated': bool(form_path),
                'contract_email_sent': contract_email_sent,
                'signature_status': signature_status,
                'form_instructions': form_instructions,
                'contract_path': contract_path,
                'form_path': form_path,
                'new_hire_name': full_name
            }
            
            logger.info(f"Paperwork process completed for {full_name} with status: {status}")
            return result
            
        except Exception as e:
            logger.error(f"Paperwork process failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'new_hire_name': new_hire_data.get('full_name', 'Unknown')
            }
    
    def _process_e_signature(self, new_hire_data: Dict[str, str], contract_path: str) -> str:
        """
        Process e-signature for the employment contract.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            contract_path: Path to the contract file
            
        Returns:
            str: Status of the signature process
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            
            # Use Gemini to generate signature request message
            prompt = f"""
            Generate a professional e-signature request message for {full_name}
            regarding their employment contract. The message should:
            1. Be urgent but polite
            2. Explain the importance of signing quickly
            3. Provide clear next steps
            4. Include contact information for questions
            
            Keep it concise and professional.
            """
            
            response = self.model.generate_content(prompt, request_options=LLM_REQUEST_OPTIONS)
            signature_message = response.text
            
            print(f"📝 Processing e-signature for {full_name}...")
            print(f"Contract: {contract_path}")
            print(f"Signature request: {signature_message}")
            
            # In a real implementation, you would integrate with an e-signature service
            # For now, we'll simulate the process
            import time
            time.sleep(1)  # Simulate processing time
            
            # Mock signature completion (in reality, this would be triggered by user action)
            signature_status = "completed"  # Could be "pending", "completed", or "failed"
            
            logger.info(f"E-signature processed for {full_name}: {signature_status}")
            return signature_status
            
        except Exception as e:
            logger.error(f"Failed to process e-signature: {e}")
            return "failed"
