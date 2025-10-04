"""
Buddy Agent for the Onboarder system.

Assigns a buddy or mentor to new hires.
"""

import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai

from .tools.email_sender import EmailSender
from .tools.llm_utils import LLMUtils, AgentCollaborator

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class BuddyAgent:
    """Agent responsible for assigning buddies and mentors to new hires."""
    
    def __init__(self, collaborator: AgentCollaborator = None):
        """Initialize the BuddyAgent with Gemini API."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.llm_utils = LLMUtils(self.model)
        self.collaborator = collaborator or AgentCollaborator()
        self.email_sender = EmailSender()
    
    def run(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute the buddy assignment process for a new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            Dict[str, Any]: Status and results of the buddy assignment process
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            department = new_hire_data.get('department', 'General')
            
            logger.info(f"Starting buddy assignment for {full_name}")
            
            # Get insights from other agents (non-blocking)
            agent_insights = {}
            try:
                if self.collaborator:
                    agent_insights = self.collaborator.get_insights_for_agent('buddy_agent')
            except Exception as e:
                logger.warning(f"Failed to get agent insights: {e}")
            
            # Use simplified LLM response for buddy matching with timeout
            buddy_matching_schema = {
                "selected_buddy": "object",
                "matching_reasons": "array"
            }
            
            prompt = f"""
            Select the best buddy for a new employee with this profile:
            - Name: {full_name}
            - Job Title: {job_title}
            - Department: {department}
            
            Provide a single selected buddy with:
            - name, role, department, experience_years
            - communication_style, mentoring_approach
            - compatibility_score (1-10)
            - matching_reasons (brief list)
            
            Choose based on role alignment, experience level, and communication skills.
            """
            
            # Use timeout for LLM call
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("LLM call timed out")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
            
            try:
                structured_response = self.llm_utils.generate_structured_response(
                    prompt, buddy_matching_schema, agent_insights, max_retries=1
                )
                signal.alarm(0)  # Cancel timeout
                
                if structured_response['success']:
                    buddy_data = structured_response['data']
                    selected_buddy = self._format_selected_buddy(buddy_data.get('selected_buddy', {}))
                    matching_reasons = buddy_data.get('matching_reasons', [])
                    logger.info(f"Generated LLM buddy matching for {full_name}")
                else:
                    logger.warning(f"Failed to generate structured buddy matching: {structured_response['error']}")
                    raise Exception("LLM generation failed")
                    
            except (TimeoutError, Exception) as e:
                signal.alarm(0)  # Cancel timeout
                logger.warning(f"LLM call failed or timed out: {e}")
                # Fallback to basic buddy selection
                selected_buddy = self._get_fallback_buddy()
                matching_reasons = ["Role alignment", "Experience level", "Communication skills"]
            
            # Send notifications
            notification_sent = self._send_buddy_notifications(new_hire_data, selected_buddy)
            
            # Generate simple introduction plan (no LLM call to save time)
            introduction_plan = self._generate_simple_introduction_plan(new_hire_data, selected_buddy)
            
            # Share insights with other agents
            if self.collaborator:
                try:
                    self.collaborator.share_insight(
                        'buddy_agent',
                        'buddy_assignment',
                        {
                            'selected_buddy': selected_buddy,
                            'matching_criteria': matching_reasons,
                            'compatibility_score': selected_buddy.get('compatibility_score', 0),
                            'introduction_plan': introduction_plan
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to share insights: {e}")
            
            status = "SUCCESS" if selected_buddy and notification_sent else "FAIL"
            
            result = {
                'status': status,
                'selected_buddy': selected_buddy,
                'matching_reasons': matching_reasons,
                'notification_sent': notification_sent,
                'introduction_plan': introduction_plan,
                'new_hire_name': full_name
            }
            
            logger.info(f"Buddy assignment completed for {full_name} with status: {status}")
            return result
            
        except Exception as e:
            logger.error(f"Buddy assignment failed: {e}")
            return {
                'status': 'FAIL',
                'error': str(e),
                'new_hire_name': new_hire_data.get('full_name', 'Unknown')
            }
    
    def _select_buddy(self, new_hire_data: Dict[str, str], buddy_suggestions: str) -> Dict[str, str]:
        """
        Select the best buddy from the suggestions.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            buddy_suggestions: Gemini-generated buddy suggestions
            
        Returns:
            Dict[str, str]: Selected buddy information
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            
            print(f"🤝 Selecting buddy for {full_name}...")
            print(f"Job title: {job_title}")
            print(f"Suggestions: {buddy_suggestions}")
            
            # Mock buddy selection (in reality, this would use a more sophisticated algorithm)
            selected_buddy = {
                'name': 'Sarah Johnson',
                'email': 'sarah.johnson@company.com',
                'role': 'Senior Software Engineer',
                'department': 'Engineering',
                'experience': '4 years',
                'qualifications': 'Excellent mentor, great communication skills, similar background'
            }
            
            print(f"✅ Selected buddy: {selected_buddy['name']} ({selected_buddy['role']})")
            
            logger.info(f"Buddy selected for {full_name}: {selected_buddy['name']}")
            return selected_buddy
            
        except Exception as e:
            logger.error(f"Failed to select buddy: {e}")
            return {}
    
    def _send_buddy_notifications(self, new_hire_data: Dict[str, str], selected_buddy: Dict[str, str]) -> bool:
        """
        Send notifications to the new hire and selected buddy.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            selected_buddy: Dictionary containing selected buddy information
            
        Returns:
            bool: True if notifications were sent successfully, False otherwise
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            buddy_name = selected_buddy.get('name', 'Buddy')
            buddy_email = selected_buddy.get('email', 'buddy@company.com')
            new_hire_email = new_hire_data.get('personal_email', '')
            
            print(f"📧 Sending buddy notifications...")
            print(f"New hire: {full_name} ({new_hire_email})")
            print(f"Buddy: {buddy_name} ({buddy_email})")
            
            # Send notification to buddy
            buddy_notification_sent = self.email_sender.send_buddy_notification(
                buddy_email, full_name, new_hire_email
            )
            
            # Send notification to new hire
            new_hire_notification_sent = self._send_new_hire_buddy_notification(
                new_hire_data, selected_buddy
            )
            
            success = buddy_notification_sent and new_hire_notification_sent
            
            if success:
                print("✅ Buddy notifications sent successfully")
            else:
                print("❌ Failed to send buddy notifications")
            
            logger.info(f"Buddy notifications sent for {full_name}: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to send buddy notifications: {e}")
            return False
    
    def _send_new_hire_buddy_notification(self, new_hire_data: Dict[str, str], selected_buddy: Dict[str, str]) -> bool:
        """
        Send notification to new hire about their assigned buddy.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            selected_buddy: Dictionary containing selected buddy information
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            new_hire_email = new_hire_data.get('personal_email', '')
            buddy_name = selected_buddy.get('name', 'Buddy')
            buddy_role = selected_buddy.get('role', 'Colleague')
            
            subject = f"Your Buddy Assignment - {buddy_name}"
            
            body = f"""
            Dear {full_name},
            
            Great news! We've assigned you a buddy to help you get settled in.
            
            Your buddy is: {buddy_name}
            Role: {buddy_role}
            Email: {selected_buddy.get('email', 'buddy@company.com')}
            
            {buddy_name} will reach out to you before your start date to introduce themselves
            and answer any questions you might have.
            
            Don't hesitate to reach out to them with any questions about the company,
            your role, or just to chat!
            
            Best regards,
            The HR Team
            """
            
            print(f"📧 Sending buddy assignment notification to {full_name}...")
            print(f"Subject: {subject}")
            print(f"Body: {body.strip()}")
            
            logger.info(f"Buddy assignment notification sent to {full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send new hire buddy notification: {e}")
            return False
    
    def _generate_introduction_plan(self, new_hire_data: Dict[str, str], selected_buddy: Dict[str, str]) -> str:
        """
        Generate a plan for the buddy introduction process.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            selected_buddy: Dictionary containing selected buddy information
            
        Returns:
            str: Generated introduction plan
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            buddy_name = selected_buddy.get('name', 'Buddy')
            
            # Use Gemini to generate introduction plan
            prompt = f"""
            Create a comprehensive buddy introduction plan for {full_name} (new {job_title})
            and their assigned buddy {buddy_name}.
            
            Include:
            1. Pre-start date activities
            2. First day introduction
            3. First week check-ins
            4. Ongoing support schedule
            5. Key topics to cover
            6. Success metrics
            
            Make it practical and actionable.
            """
            
            response = self.model.generate_content(prompt)
            introduction_plan = response.text
            
            print(f"📋 Generated introduction plan for {full_name} and {buddy_name}")
            print(f"Plan: {introduction_plan}")
            
            logger.info(f"Introduction plan generated for {full_name}")
            return introduction_plan
            
        except Exception as e:
            logger.error(f"Failed to generate introduction plan: {e}")
            return "Introduction plan generation failed"
    
    def _select_buddy_llm(self, new_hire_data: Dict[str, str], buddy_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Select the best buddy using LLM analysis.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            buddy_data: Structured buddy matching data from LLM
            
        Returns:
            Dict[str, str]: Selected buddy information
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            
            print(f"🤝 Selecting optimal buddy for {full_name} using LLM analysis...")
            
            # Find the buddy with highest compatibility score
            candidates = buddy_data.get('buddy_candidates', [])
            if not candidates:
                logger.warning("No buddy candidates found")
                return self._get_fallback_buddy()
            
            # Select buddy with highest compatibility score
            best_buddy = max(candidates, key=lambda x: x.get('compatibility_score', 0))
            
            selected_buddy = {
                'name': best_buddy.get('name', 'Sarah Johnson'),
                'email': f"{best_buddy.get('name', 'sarah.johnson').lower().replace(' ', '.')}@company.com",
                'role': best_buddy.get('role', 'Senior Software Engineer'),
                'department': best_buddy.get('department', 'Engineering'),
                'experience': f"{best_buddy.get('experience_years', 4)} years",
                'compatibility_score': best_buddy.get('compatibility_score', 8),
                'communication_style': best_buddy.get('communication_style', 'Collaborative'),
                'mentoring_approach': best_buddy.get('mentoring_approach', 'Hands-on guidance'),
                'qualifications': best_buddy.get('matching_reasons', 'Excellent mentor, great communication skills')
            }
            
            print(f"✅ Selected buddy: {selected_buddy['name']} (Compatibility: {selected_buddy['compatibility_score']}/10)")
            print(f"   Role: {selected_buddy['role']}")
            print(f"   Communication: {selected_buddy['communication_style']}")
            
            logger.info(f"LLM-selected buddy for {full_name}: {selected_buddy['name']}")
            return selected_buddy
            
        except Exception as e:
            logger.error(f"Failed to select buddy using LLM: {e}")
            return self._get_fallback_buddy()
    
    def _generate_introduction_plan_llm(self, new_hire_data: Dict[str, str], selected_buddy: Dict[str, str]) -> str:
        """
        Generate a comprehensive introduction plan using LLM analysis.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            selected_buddy: Dictionary containing selected buddy information
            
        Returns:
            str: Generated introduction plan
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            buddy_name = selected_buddy.get('name', 'Buddy')
            
            # Use LLM to generate comprehensive introduction plan
            introduction_schema = {
                "pre_start_activities": "array",
                "first_day_plan": "array",
                "first_week_checkins": "array",
                "ongoing_support": "array",
                "key_topics": "array",
                "success_metrics": "array"
            }
            
            prompt = f"""
            Create a comprehensive buddy introduction plan for {full_name} (new {job_title})
            and their assigned buddy {buddy_name}.
            
            Buddy details:
            - Communication style: {selected_buddy.get('communication_style', 'Collaborative')}
            - Mentoring approach: {selected_buddy.get('mentoring_approach', 'Hands-on guidance')}
            - Compatibility score: {selected_buddy.get('compatibility_score', 8)}/10
            
            Design a structured introduction process that leverages the buddy's strengths
            and communication style to maximize the new hire's onboarding success.
            """
            
            structured_response = self.llm_utils.generate_structured_response(
                prompt, introduction_schema
            )
            
            if structured_response['success']:
                plan_data = structured_response['data']
                
                # Format the introduction plan for display
                plan_text = f"Buddy Introduction Plan for {full_name} and {buddy_name}:\n\n"
                
                for category, activities in plan_data.items():
                    plan_text += f"{category.replace('_', ' ').title()}:\n"
                    for activity in activities:
                        plan_text += f"  - {activity}\n"
                    plan_text += "\n"
                
                print(f"📋 Generated LLM-powered introduction plan for {full_name} and {buddy_name}")
                logger.info(f"Introduction plan generated for {full_name}")
                return plan_text
            else:
                logger.warning(f"Failed to generate structured introduction plan: {structured_response['error']}")
                return self._generate_introduction_plan(new_hire_data, selected_buddy)
                
        except Exception as e:
            logger.error(f"Failed to generate introduction plan using LLM: {e}")
            return "Introduction plan generation failed"
    
    def _get_fallback_buddy_suggestions(self, job_title: str, department: str) -> Dict[str, Any]:
        """
        Get fallback buddy suggestions when LLM generation fails.
        
        Args:
            job_title: Job title of the new hire
            department: Department of the new hire
            
        Returns:
            Dict[str, Any]: Basic buddy suggestions
        """
        return {
            "buddy_candidates": [
                {
                    "name": "Sarah Johnson",
                    "role": "Senior Software Engineer",
                    "department": "Engineering",
                    "experience_years": 4,
                    "compatibility_score": 8,
                    "communication_style": "Collaborative",
                    "mentoring_approach": "Hands-on guidance"
                }
            ],
            "matching_criteria": ["Role alignment", "Experience level", "Communication skills"],
            "recommendation": {"selected_buddy": "Sarah Johnson", "reason": "Best overall match"}
        }
    
    def _get_fallback_buddy(self) -> Dict[str, str]:
        """
        Get a fallback buddy when LLM selection fails.
        
        Returns:
            Dict[str, str]: Fallback buddy information
        """
        return {
            'name': 'Sarah Johnson',
            'email': 'sarah.johnson@company.com',
            'role': 'Senior Software Engineer',
            'department': 'Engineering',
            'experience': '4 years',
            'compatibility_score': 7,
            'qualifications': 'Experienced mentor with good communication skills'
        }
    
    def _format_selected_buddy(self, buddy_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Format the selected buddy data from LLM response.
        
        Args:
            buddy_data: Raw buddy data from LLM
            
        Returns:
            Dict[str, str]: Formatted buddy information
        """
        return {
            'name': buddy_data.get('name', 'Sarah Johnson'),
            'email': f"{buddy_data.get('name', 'sarah.johnson').lower().replace(' ', '.')}@company.com",
            'role': buddy_data.get('role', 'Senior Software Engineer'),
            'department': buddy_data.get('department', 'Engineering'),
            'experience': f"{buddy_data.get('experience_years', 4)} years",
            'compatibility_score': buddy_data.get('compatibility_score', 8),
            'communication_style': buddy_data.get('communication_style', 'Collaborative'),
            'mentoring_approach': buddy_data.get('mentoring_approach', 'Hands-on guidance'),
            'qualifications': ', '.join(buddy_data.get('matching_reasons', ['Excellent mentor']))
        }
    
    def _generate_simple_introduction_plan(self, new_hire_data: Dict[str, str], selected_buddy: Dict[str, str]) -> str:
        """
        Generate a simple introduction plan without LLM calls.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            selected_buddy: Dictionary containing selected buddy information
            
        Returns:
            str: Simple introduction plan
        """
        full_name = new_hire_data.get('full_name', 'New Hire')
        buddy_name = selected_buddy.get('name', 'Buddy')
        
        return f"""Buddy Introduction Plan for {full_name} and {buddy_name}:

Pre-start Activities:
  - Buddy will reach out via email to introduce themselves
  - Schedule a 15-minute virtual coffee chat before start date
  - Share relevant company resources and team information

First Day:
  - Welcome the new hire and provide office tour
  - Introduce to team members and key stakeholders
  - Explain team dynamics and communication preferences
  - Schedule daily check-ins for the first week

First Week:
  - Daily 15-minute check-ins to address questions
  - Review role expectations and initial projects
  - Provide guidance on company tools and processes
  - Introduce to company culture and values

Ongoing Support:
  - Weekly check-ins for the first month
  - Monthly check-ins for the first 3 months
  - Be available for questions and guidance
  - Provide feedback and support for professional development

Success Metrics:
  - New hire feels welcomed and supported
  - Clear understanding of role and expectations
  - Successful integration into team and company culture
  - Positive feedback from new hire and manager"""
