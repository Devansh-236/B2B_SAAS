"""
Tools package for the Onboarder system.

Contains utility modules for email sending, document generation, and calendar management.
"""

from .email_sender import EmailSender
from .document_generator import DocumentGenerator
from .calendar_manager import CalendarManager

__all__ = ['EmailSender', 'DocumentGenerator', 'CalendarManager']
