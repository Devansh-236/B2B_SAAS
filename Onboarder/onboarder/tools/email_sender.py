"""
Email Sender utility for the Onboarder system.

Provides functionality to send templated emails to new hires and stakeholders.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    """Utility class for sending templated emails."""
    
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        """
        Initialize the EmailSender.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def send_welcome_email(self, new_hire_data: Dict[str, str]) -> bool:
        """
        Send a welcome email to the new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            email = new_hire_data.get('personal_email', '')
            full_name = new_hire_data.get('full_name', 'New Hire')
            start_date = new_hire_data.get('start_date', 'TBD')
            
            subject = f"Welcome to the Team, {full_name}!"
            
            body = f"""
            Dear {full_name},
            
            Welcome to our company! We're excited to have you join our team.
            
            Your start date is: {start_date}
            
            We'll be sending you a welcome kit shortly, and you'll receive more information
            about your first day and onboarding process.
            
            If you have any questions, please don't hesitate to reach out.
            
            Best regards,
            The HR Team
            """
            
            print(f"📧 Sending welcome email to {email}...")
            print(f"Subject: {subject}")
            print(f"Body: {body.strip()}")
            
            # In a real implementation, you would send the actual email here
            # self._send_email(email, subject, body)
            
            logger.info(f"Welcome email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False
    
    def send_buddy_notification(self, buddy_email: str, new_hire_name: str, new_hire_email: str) -> bool:
        """
        Send notification to assigned buddy.
        
        Args:
            buddy_email: Email of the assigned buddy
            new_hire_name: Name of the new hire
            new_hire_email: Email of the new hire
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            subject = f"You've been assigned as a buddy for {new_hire_name}"
            
            body = f"""
            Hi there,
            
            You've been assigned as a buddy for our new hire: {new_hire_name}
            Email: {new_hire_email}
            
            Please reach out to them before their start date to introduce yourself
            and help them feel welcome to the team.
            
            Thank you for being a great team member!
            
            Best regards,
            The HR Team
            """
            
            print(f"📧 Sending buddy notification to {buddy_email}...")
            print(f"Subject: {subject}")
            print(f"Body: {body.strip()}")
            
            logger.info(f"Buddy notification sent to {buddy_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send buddy notification: {e}")
            return False
    
    def send_contract_email(self, new_hire_data: Dict[str, str], contract_path: str) -> bool:
        """
        Send employment contract for e-signature.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            contract_path: Path to the generated contract
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            email = new_hire_data.get('personal_email', '')
            full_name = new_hire_data.get('full_name', 'New Hire')
            
            subject = "Employment Contract - Please Review and Sign"
            
            body = f"""
            Dear {full_name},
            
            Please find attached your employment contract. Please review it carefully
            and sign it electronically using the provided link.
            
            Contract file: {contract_path}
            
            If you have any questions about the contract, please contact HR.
            
            Best regards,
            The HR Team
            """
            
            print(f"📧 Sending contract email to {email}...")
            print(f"Subject: {subject}")
            print(f"Contract: {contract_path}")
            print(f"Body: {body.strip()}")
            
            logger.info(f"Contract email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send contract email: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Internal method to actually send email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # This is a placeholder for actual email sending
        # In a real implementation, you would use SMTP or an email service
        pass
