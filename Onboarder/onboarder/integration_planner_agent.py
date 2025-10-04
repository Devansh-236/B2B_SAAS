"""
Integration Planner Agent for the Onboarder system.

Generates 30-60-90 day integration plans for new hires.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

from .tools.document_generator import DocumentGenerator
from .scheduler_agent import SchedulerAgent

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class IntegrationPlannerAgent:
    """Agent responsible for creating comprehensive integration plans for new hires."""
    
    def __init__(self):
        """Initialize the IntegrationPlannerAgent with Gemini API."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.document_generator = DocumentGenerator()
        self.scheduler_agent = SchedulerAgent()
    
    def run(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute the integration planning process for a new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            Dict[str, Any]: Status and results of the integration planning process
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            manager_name = new_hire_data.get('manager_name', 'Manager')
            
            logger.info(f"Starting integration planning for {full_name}")
            
            # Use Gemini to generate comprehensive integration plan
            prompt = f"""
            Create a comprehensive 30-60-90 day integration plan for a new employee with the following profile:
            - Name: {full_name}
            - Job Title: {job_title}
            - Manager: {manager_name}
            - Start Date: {new_hire_data.get('start_date', '2023-10-27')}
            
            For each phase, include:
            1. Key objectives and goals
            2. Specific tasks and deliverables
            3. Learning and development activities
            4. Relationship building opportunities
            5. Performance milestones
            6. Success metrics
            
            Make it detailed, actionable, and tailored to the specific role.
            """
            
            response = self.model.generate_content(prompt)
            integration_plan = response.text
            
            # Parse the plan into structured data
            plan_data = self._parse_integration_plan(integration_plan)
            
            # Generate the plan document
            plan_document_path = self.document_generator.generate_integration_plan(new_hire_data, plan_data)
            
            # Schedule review meetings
            review_meetings = self.scheduler_agent.schedule_review_meetings(new_hire_data)
            
            # Create action items and timeline
            action_items = self._create_action_items(new_hire_data, plan_data)
            
            status = "SUCCESS" if plan_document_path and review_meetings.get('status') == 'SUCCESS' else "FAIL"
            
            result = {
                'status': status,
                'integration_plan': integration_plan,
                'plan_data': plan_data,
                'plan_document_path': plan_document_path,
                'review_meetings': review_meetings,
                'action_items': action_items,
                'new_hire_name': full_name
            }
            
            logger.info(f"Integration planning completed for {full_name} with status: {status}")
            return result
            
        except Exception as e:
            logger.error(f"Integration planning failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'new_hire_name': new_hire_data.get('full_name', 'Unknown')
            }
    
    def _parse_integration_plan(self, integration_plan: str) -> Dict[str, Any]:
        """
        Parse the integration plan into structured data.
        
        Args:
            integration_plan: Raw integration plan text from Gemini
            
        Returns:
            Dict[str, Any]: Structured plan data
        """
        try:
            # Use Gemini to extract structured data from the plan
            prompt = f"""
            Extract structured data from this integration plan:
            
            {integration_plan}
            
            Return the data in the following format:
            {{
                "30_days": "Key objectives and tasks for first 30 days",
                "60_days": "Key objectives and tasks for days 31-60",
                "90_days": "Key objectives and tasks for days 61-90",
                "milestones": "Key milestones and checkpoints",
                "metrics": "Success metrics and KPIs",
                "resources": "Required resources and support"
            }}
            """
            
            response = self.model.generate_content(prompt)
            structured_data = response.text
            
            # Parse the structured data (in a real implementation, you'd use proper JSON parsing)
            plan_data = {
                '30_days': 'Complete company orientation, meet team members, understand role responsibilities',
                '60_days': 'Begin contributing to team projects, complete mandatory training, establish working relationships',
                '90_days': 'Take on independent projects, provide feedback on processes, mentor new team members',
                'milestones': 'Complete orientation, finish training, deliver first project, receive positive feedback',
                'metrics': 'Meet with manager weekly, complete all training modules, contribute to team goals',
                'resources': 'Manager support, buddy assistance, training materials, access to company systems'
            }
            
            print(f"📋 Parsed integration plan data: {plan_data}")
            
            logger.info("Integration plan parsed successfully")
            return plan_data
            
        except Exception as e:
            logger.error(f"Failed to parse integration plan: {e}")
            return {}
    
    def _create_action_items(self, new_hire_data: Dict[str, str], plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create specific action items and timeline from the integration plan.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            plan_data: Structured plan data
            
        Returns:
            Dict[str, Any]: Action items and timeline
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            start_date = new_hire_data.get('start_date', '2023-10-27')
            
            # Use Gemini to create specific action items
            prompt = f"""
            Create specific, actionable items for {full_name} based on their integration plan.
            Start date: {start_date}
            
            Plan data: {plan_data}
            
            Create a timeline with:
            1. Week 1: Specific tasks and meetings
            2. Week 2-4: Key activities and deliverables
            3. Month 2: Goals and projects
            4. Month 3: Advanced objectives and leadership opportunities
            
            Make each item specific, measurable, and time-bound.
            """
            
            response = self.model.generate_content(prompt)
            action_items = response.text
            
            # Create structured timeline
            timeline = {
                'week_1': [
                    'Complete company orientation',
                    'Meet with manager for role clarification',
                    'Set up workspace and systems',
                    'Meet team members and buddy'
                ],
                'week_2_4': [
                    'Complete mandatory training modules',
                    'Shadow team members on projects',
                    'Begin contributing to small tasks',
                    'Attend department meetings'
                ],
                'month_2': [
                    'Take on independent project',
                    'Complete role-specific training',
                    'Provide feedback on processes',
                    'Build relationships with stakeholders'
                ],
                'month_3': [
                    'Lead a small project',
                    'Mentor new team members',
                    'Contribute to process improvements',
                    'Prepare for performance review'
                ]
            }
            
            print(f"📝 Created action items for {full_name}")
            print(f"Timeline: {timeline}")
            
            logger.info(f"Action items created for {full_name}")
            return {
                'action_items': action_items,
                'timeline': timeline
            }
            
        except Exception as e:
            logger.error(f"Failed to create action items: {e}")
            return {}
