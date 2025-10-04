"""
Scheduler Agent for the Onboarder system.

Arranges all meetings and orientation sessions for new hires.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

from .tools.calendar_manager import CalendarManager

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SchedulerAgent:
    """Agent responsible for scheduling meetings and orientation sessions."""
    
    def __init__(self):
        """Initialize the SchedulerAgent with Gemini API."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.calendar_manager = CalendarManager()
    
    def run(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute the scheduling process for a new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            Dict[str, Any]: Status and results of the scheduling process
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            start_date = new_hire_data.get('start_date', '2023-10-27')
            
            logger.info(f"Starting scheduling process for {full_name}")
            
            # Use Gemini to generate personalized meeting schedule
            prompt = f"""
            Create a comprehensive first-week meeting schedule for a new employee named {full_name}
            with job title "{new_hire_data.get('job_title', 'Employee')}" starting on {start_date}.
            
            Include:
            1. Orientation meeting (first day)
            2. Manager 1-on-1 (second day)
            3. Team introduction (third day)
            4. Department overview (fourth day)
            5. HR benefits session (fifth day)
            
            For each meeting, suggest:
            - Optimal time of day
            - Duration
            - Key topics to cover
            - Attendees
            
            Format as a structured schedule.
            """
            
            response = self.model.generate_content(prompt)
            meeting_schedule = response.text
            
            # Schedule orientation meeting
            orientation_success = self.calendar_manager.schedule_orientation_meeting(new_hire_data, start_date)
            
            # Schedule manager 1-on-1
            manager_1on1_success = self.calendar_manager.schedule_manager_1on1(new_hire_data, start_date)
            
            # Schedule team intro meeting
            team_intro_success = self.calendar_manager.schedule_team_intro_meeting(new_hire_data, start_date)
            
            # Schedule additional meetings
            additional_meetings = self._schedule_additional_meetings(new_hire_data, start_date)
            
            all_meetings_scheduled = all([
                orientation_success,
                manager_1on1_success,
                team_intro_success,
                additional_meetings
            ])
            
            status = "SUCCESS" if all_meetings_scheduled else "FAIL"
            
            result = {
                'status': status,
                'meeting_schedule': meeting_schedule,
                'orientation_scheduled': orientation_success,
                'manager_1on1_scheduled': manager_1on1_success,
                'team_intro_scheduled': team_intro_success,
                'additional_meetings_scheduled': additional_meetings,
                'new_hire_name': full_name
            }
            
            logger.info(f"Scheduling process completed for {full_name} with status: {status}")
            return result
            
        except Exception as e:
            logger.error(f"Scheduling process failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'new_hire_name': new_hire_data.get('full_name', 'Unknown')
            }
    
    def _schedule_additional_meetings(self, new_hire_data: Dict[str, str], start_date: str) -> bool:
        """
        Schedule additional meetings for the first week.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            start_date: Start date for the new hire
            
        Returns:
            bool: True if additional meetings were scheduled successfully, False otherwise
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            
            print(f"📅 Scheduling additional meetings for {full_name}...")
            
            # Use Gemini to suggest additional meetings based on role
            prompt = f"""
            Suggest 2-3 additional meetings for a new {job_title} in their first week.
            Consider role-specific training, department introductions, and skill assessments.
            For each meeting, suggest timing, duration, and key objectives.
            """
            
            response = self.model.generate_content(prompt)
            additional_meetings = response.text
            
            print(f"Additional meetings suggested: {additional_meetings}")
            
            # Mock scheduling additional meetings
            meetings = [
                f"Department Overview - {full_name}",
                f"Role-specific Training - {full_name}",
                f"HR Benefits Session - {full_name}"
            ]
            
            for meeting in meetings:
                print(f"  ✅ {meeting}: Scheduled")
            
            logger.info(f"Additional meetings scheduled for {full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule additional meetings: {e}")
            return False
    
    def schedule_review_meetings(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Schedule 30, 60, and 90-day review meetings.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            Dict[str, Any]: Status and results of review meeting scheduling
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            start_date = new_hire_data.get('start_date', '2023-10-27')
            
            logger.info(f"Scheduling review meetings for {full_name}")
            
            # Schedule review meetings
            review_results = self.calendar_manager.schedule_review_meetings(new_hire_data, start_date)
            
            # Use Gemini to generate review meeting agendas
            prompt = f"""
            Generate agendas for 30, 60, and 90-day review meetings for {full_name}
            in the role of {new_hire_data.get('job_title', 'Employee')}.
            
            For each review, include:
            1. Key discussion topics
            2. Performance metrics to review
            3. Goal setting activities
            4. Feedback collection
            5. Next steps planning
            
            Format as separate agendas for each review period.
            """
            
            response = self.model.generate_content(prompt)
            review_agendas = response.text
            
            all_reviews_scheduled = all(review_results)
            
            status = "SUCCESS" if all_reviews_scheduled else "FAIL"
            
            result = {
                'status': status,
                'review_meetings_scheduled': review_results,
                'review_agendas': review_agendas,
                'new_hire_name': full_name
            }
            
            logger.info(f"Review meetings scheduled for {full_name} with status: {status}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to schedule review meetings: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'new_hire_name': new_hire_data.get('full_name', 'Unknown')
            }
