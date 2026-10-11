"""
Training Agent for the Onboarder system.

Enrolls new hires in mandatory training programs.
"""

import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai

from .tools.llm_utils import LLMUtils, AgentCollaborator, LLM_REQUEST_OPTIONS

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TrainingAgent:
    """Agent responsible for enrolling new hires in training programs."""
    
    def __init__(self, collaborator: AgentCollaborator = None):
        """Initialize the TrainingAgent with Gemini API."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.llm_utils = LLMUtils(self.model)
        self.collaborator = collaborator or AgentCollaborator()
    
    def run(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Execute the training enrollment process for a new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            Dict[str, Any]: Status and results of the training enrollment process
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            department = new_hire_data.get('department', 'General')
            
            logger.info(f"Starting training enrollment for {full_name}")
            
            # Get insights from other agents
            agent_insights = self.collaborator.get_insights_for_agent('training_agent')
            
            # Use structured LLM response to determine required training
            training_schema = {
                "mandatory_courses": "array",
                "role_specific_courses": "array", 
                "department_courses": "array",
                "compliance_courses": "array",
                "recommended_learning_path": "array",
                "assessment_requirements": "array"
            }
            
            prompt = f"""
            Analyze the training requirements for a new employee with this profile:
            - Name: {full_name}
            - Job Title: {job_title}
            - Department: {department}
            
            For each category, provide courses with: course_name, duration_hours, priority_level, 
            deadline_weeks, delivery_method, prerequisites, and learning_objectives.
            
            Consider industry standards, role complexity, and career development paths.
            """
            
            structured_response = self.llm_utils.generate_structured_response(
                prompt, training_schema, agent_insights
            )
            
            if structured_response['success']:
                training_requirements = structured_response['data']
                logger.info(f"Generated structured training requirements for {full_name}")
            else:
                logger.warning(f"Failed to generate structured training requirements: {structured_response['error']}")
                # Fallback to basic training requirements
                training_requirements = self._get_fallback_training_requirements(job_title, department)
            
            # Enroll in mandatory training using LLM-driven logic
            enrollment_results = self._enroll_in_training_llm(new_hire_data, training_requirements)
            
            # Generate training schedule using structured LLM response
            training_schedule = self._generate_training_schedule_llm(new_hire_data, enrollment_results)
            
            # Create learning path using LLM analysis
            learning_path = self._create_learning_path_llm(new_hire_data, job_title, training_requirements)
            
            # Share insights with other agents
            self.collaborator.share_insight(
                'training_agent', 
                'training_requirements', 
                {
                    'courses': training_requirements,
                    'enrollment_status': enrollment_results,
                    'learning_path': learning_path
                }
            )
            
            status = "SUCCESS" if enrollment_results else "FAIL"
            
            result = {
                'status': status,
                'training_requirements': training_requirements,
                'enrollment_results': enrollment_results,
                'training_schedule': training_schedule,
                'learning_path': learning_path,
                'new_hire_name': full_name
            }
            
            logger.info(f"Training enrollment completed for {full_name} with status: {status}")
            return result
            
        except Exception as e:
            logger.error(f"Training enrollment failed: {e}")
            # Generate error recovery strategy
            recovery_strategy = self.llm_utils.generate_error_recovery_strategy(
                {'operation': 'training_enrollment', 'error': str(e)},
                'training_enrollment'
            )
            return {
                'status': 'FAIL',
                'error': str(e),
                'new_hire_name': new_hire_data.get('full_name', 'Unknown'),
                'recovery_strategy': recovery_strategy
            }
    
    def _enroll_in_training(self, new_hire_data: Dict[str, str], training_requirements: str) -> List[Dict[str, Any]]:
        """
        Enroll the new hire in required training courses.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            training_requirements: Gemini-generated training requirements
            
        Returns:
            List[Dict[str, Any]]: List of enrollment results
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            
            print(f"📚 Enrolling {full_name} in training courses...")
            print(f"Job title: {job_title}")
            print(f"Requirements: {training_requirements}")
            
            # Mock training courses based on role
            mandatory_courses = [
                {
                    'name': 'Company Code of Conduct',
                    'duration': '2 hours',
                    'priority': 'High',
                    'deadline': 'First week',
                    'method': 'Online',
                    'enrolled': True
                },
                {
                    'name': 'Workplace Safety Training',
                    'duration': '1 hour',
                    'priority': 'High',
                    'deadline': 'First week',
                    'method': 'Online',
                    'enrolled': True
                },
                {
                    'name': 'Anti-Harassment Training',
                    'duration': '1.5 hours',
                    'priority': 'High',
                    'deadline': 'First week',
                    'method': 'Online',
                    'enrolled': True
                }
            ]
            
            # Add role-specific training
            if 'engineer' in job_title.lower() or 'developer' in job_title.lower():
                mandatory_courses.extend([
                    {
                        'name': 'Software Development Best Practices',
                        'duration': '4 hours',
                        'priority': 'High',
                        'deadline': 'First month',
                        'method': 'Online',
                        'enrolled': True
                    },
                    {
                        'name': 'Version Control with Git',
                        'duration': '3 hours',
                        'priority': 'Medium',
                        'deadline': 'First month',
                        'method': 'Online',
                        'enrolled': True
                    }
                ])
            elif 'sales' in job_title.lower():
                mandatory_courses.extend([
                    {
                        'name': 'Sales Process Training',
                        'duration': '6 hours',
                        'priority': 'High',
                        'deadline': 'First month',
                        'method': 'Hybrid',
                        'enrolled': True
                    },
                    {
                        'name': 'CRM System Training',
                        'duration': '2 hours',
                        'priority': 'High',
                        'deadline': 'First week',
                        'method': 'Online',
                        'enrolled': True
                    }
                ])
            
            # Display enrollment results
            for course in mandatory_courses:
                status = "✅" if course['enrolled'] else "❌"
                print(f"  {status} {course['name']} ({course['duration']}) - {course['method']}")
            
            logger.info(f"Training enrollment completed for {full_name}")
            return mandatory_courses
            
        except Exception as e:
            logger.error(f"Failed to enroll in training: {e}")
            return []
    
    def _generate_training_schedule(self, new_hire_data: Dict[str, str], enrollment_results: List[Dict[str, Any]]) -> str:
        """
        Generate a training schedule for the new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            enrollment_results: List of enrolled courses
            
        Returns:
            str: Generated training schedule
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            start_date = new_hire_data.get('start_date', '2023-10-27')
            
            # Use Gemini to generate training schedule
            prompt = f"""
            Create a training schedule for {full_name} starting on {start_date}.
            They are enrolled in the following courses:
            
            {enrollment_results}
            
            Create a realistic schedule that:
            1. Spreads training over the first month
            2. Prioritizes high-priority courses
            3. Balances workload with other onboarding activities
            4. Includes time for practice and reflection
            
            Format as a weekly schedule with specific dates and times.
            """
            
            response = self.model.generate_content(prompt, request_options=LLM_REQUEST_OPTIONS)
            training_schedule = response.text
            
            print(f"📅 Generated training schedule for {full_name}")
            print(f"Schedule: {training_schedule}")
            
            logger.info(f"Training schedule generated for {full_name}")
            return training_schedule
            
        except Exception as e:
            logger.error(f"Failed to generate training schedule: {e}")
            return "Training schedule generation failed"
    
    def _create_learning_path(self, new_hire_data: Dict[str, str], job_title: str) -> str:
        """
        Create a personalized learning path for the new hire.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            job_title: Job title of the new hire
            
        Returns:
            str: Generated learning path
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            
            # Use Gemini to create learning path
            prompt = f"""
            Create a comprehensive learning path for {full_name} in the role of {job_title}.
            
            Include:
            1. Immediate learning goals (first 30 days)
            2. Short-term goals (30-90 days)
            3. Long-term development goals (3-6 months)
            4. Recommended resources and courses
            5. Skill assessments and milestones
            6. Mentorship opportunities
            
            Make it personalized and actionable.
            """
            
            response = self.model.generate_content(prompt, request_options=LLM_REQUEST_OPTIONS)
            learning_path = response.text
            
            print(f"🎯 Created learning path for {full_name}")
            print(f"Learning path: {learning_path}")
            
            logger.info(f"Learning path created for {full_name}")
            return learning_path
            
        except Exception as e:
            logger.error(f"Failed to create learning path: {e}")
            return "Learning path creation failed"
    
    def _enroll_in_training_llm(self, new_hire_data: Dict[str, str], training_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Enroll the new hire in required training courses using LLM-driven logic.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            training_requirements: Structured training requirements from LLM
            
        Returns:
            List[Dict[str, Any]]: List of enrollment results
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            job_title = new_hire_data.get('job_title', 'Employee')
            
            print(f"📚 Enrolling {full_name} in LLM-generated training courses...")
            
            # Use LLM to determine enrollment priority and conflicts
            enrollment_schema = {
                "enrollment_plan": "array",
                "conflict_resolution": "array",
                "prerequisite_handling": "array",
                "timeline_optimization": "object"
            }
            
            prompt = f"""
            Create an enrollment plan for {full_name} ({job_title}) based on these training requirements:
            {training_requirements}
            
            For each course, determine:
            - enrollment_priority (1-10)
            - optimal_start_date
            - prerequisite_satisfaction
            - potential_conflicts
            - enrollment_status (enrolled/pending/failed)
            
            Optimize the timeline to avoid conflicts and ensure prerequisites are met.
            """
            
            structured_response = self.llm_utils.generate_structured_response(
                prompt, enrollment_schema
            )
            
            if structured_response['success']:
                enrollment_plan = structured_response['data']
                
                # Process the enrollment plan
                enrollment_results = []
                for course_plan in enrollment_plan.get('enrollment_plan', []):
                    enrollment_results.append({
                        'course_name': course_plan.get('course_name', 'Unknown'),
                        'duration_hours': course_plan.get('duration_hours', 1),
                        'priority': course_plan.get('enrollment_priority', 5),
                        'deadline': course_plan.get('optimal_start_date', 'First week'),
                        'method': course_plan.get('delivery_method', 'Online'),
                        'enrolled': course_plan.get('enrollment_status') == 'enrolled',
                        'prerequisites_met': course_plan.get('prerequisite_satisfaction', True),
                        'conflicts': course_plan.get('potential_conflicts', [])
                    })
                
                # Display enrollment results
                for course in enrollment_results:
                    status = "✅" if course['enrolled'] else "⏳" if course['enrolled'] == False else "❌"
                    print(f"  {status} {course['course_name']} ({course['duration_hours']}h) - {course['method']}")
                
                logger.info(f"LLM-driven training enrollment completed for {full_name}")
                return enrollment_results
            else:
                logger.warning(f"Failed to generate enrollment plan: {structured_response['error']}")
                return self._enroll_in_training(new_hire_data, str(training_requirements))
                
        except Exception as e:
            logger.error(f"Failed to enroll in training using LLM: {e}")
            # Malformed LLM output should not fail the whole phase; use the basic enrollment
            return self._enroll_in_training(new_hire_data, str(training_requirements))
    
    def _generate_training_schedule_llm(self, new_hire_data: Dict[str, str], enrollment_results: List[Dict[str, Any]]) -> str:
        """
        Generate a training schedule using LLM analysis.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            enrollment_results: List of enrolled courses
            
        Returns:
            str: Generated training schedule
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            start_date = new_hire_data.get('start_date', '2023-10-27')
            
            # Use LLM to generate optimized training schedule
            schedule_schema = {
                "weekly_schedule": "array",
                "milestone_dates": "array",
                "assessment_schedule": "array",
                "flexibility_options": "array"
            }
            
            prompt = f"""
            Create an optimized training schedule for {full_name} starting {start_date}.
            Enrolled courses: {enrollment_results}
            
            Generate a weekly schedule that:
            1. Balances workload with other onboarding activities
            2. Respects course prerequisites
            3. Minimizes conflicts
            4. Includes practice time and assessments
            5. Provides flexibility for unexpected delays
            
            For each week, specify courses, duration, and learning objectives.
            """
            
            structured_response = self.llm_utils.generate_structured_response(
                prompt, schedule_schema
            )
            
            if structured_response['success']:
                schedule_data = structured_response['data']
                
                # Format the schedule for display
                schedule_text = f"Training Schedule for {full_name}:\n\n"
                
                for week_plan in schedule_data.get('weekly_schedule', []):
                    schedule_text += f"Week {week_plan.get('week_number', 'N/A')}:\n"
                    for course in week_plan.get('courses', []):
                        schedule_text += f"  - {course.get('course_name', 'Unknown')}: {course.get('duration', '1h')}\n"
                        schedule_text += f"    Objectives: {course.get('learning_objectives', 'N/A')}\n"
                    schedule_text += "\n"
                
                print(f"📅 Generated LLM-optimized training schedule for {full_name}")
                logger.info(f"Training schedule generated for {full_name}")
                return schedule_text
            else:
                logger.warning(f"Failed to generate structured schedule: {structured_response['error']}")
                return self._generate_training_schedule(new_hire_data, enrollment_results)
                
        except Exception as e:
            logger.error(f"Failed to generate training schedule using LLM: {e}")
            return "Training schedule generation failed"
    
    def _create_learning_path_llm(self, new_hire_data: Dict[str, str], job_title: str, training_requirements: Dict[str, Any]) -> str:
        """
        Create a personalized learning path using LLM analysis.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            job_title: Job title of the new hire
            training_requirements: Structured training requirements
            
        Returns:
            str: Generated learning path
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            
            # Use LLM to create comprehensive learning path
            learning_path_schema = {
                "immediate_goals": "array",
                "short_term_goals": "array", 
                "long_term_goals": "array",
                "skill_development": "array",
                "mentorship_opportunities": "array",
                "career_progression": "array"
            }
            
            prompt = f"""
            Create a comprehensive learning path for {full_name} in the role of {job_title}.
            Training requirements: {training_requirements}
            
            Design a progressive learning journey that includes:
            1. Immediate learning goals (first 30 days)
            2. Short-term development goals (30-90 days)
            3. Long-term career development goals (3-6 months)
            4. Specific skill development areas
            5. Mentorship and collaboration opportunities
            6. Career progression milestones
            
            Make it personalized, actionable, and aligned with the role requirements.
            """
            
            structured_response = self.llm_utils.generate_structured_response(
                prompt, learning_path_schema
            )
            
            if structured_response['success']:
                learning_path_data = structured_response['data']
                
                # Format the learning path for display
                path_text = f"Learning Path for {full_name}:\n\n"
                
                for category, goals in learning_path_data.items():
                    path_text += f"{category.replace('_', ' ').title()}:\n"
                    for goal in goals:
                        path_text += f"  - {goal}\n"
                    path_text += "\n"
                
                print(f"🎯 Created LLM-generated learning path for {full_name}")
                logger.info(f"Learning path created for {full_name}")
                return path_text
            else:
                logger.warning(f"Failed to generate structured learning path: {structured_response['error']}")
                return self._create_learning_path(new_hire_data, job_title)
                
        except Exception as e:
            logger.error(f"Failed to create learning path using LLM: {e}")
            return "Learning path creation failed"
    
    def _get_fallback_training_requirements(self, job_title: str, department: str) -> Dict[str, Any]:
        """
        Get fallback training requirements when LLM generation fails.
        
        Args:
            job_title: Job title of the new hire
            department: Department of the new hire
            
        Returns:
            Dict[str, Any]: Basic training requirements
        """
        return {
            "mandatory_courses": [
                {
                    "course_name": "Company Code of Conduct",
                    "duration_hours": 2,
                    "priority_level": "High",
                    "deadline_weeks": 1,
                    "delivery_method": "Online"
                }
            ],
            "role_specific_courses": [],
            "department_courses": [],
            "compliance_courses": [],
            "recommended_learning_path": [],
            "assessment_requirements": []
        }
