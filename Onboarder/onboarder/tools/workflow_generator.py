"""
Dynamic Workflow Generator for the Onboarder system.

Generates personalized onboarding workflows based on LLM analysis of role, 
experience level, and company context.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import google.generativeai as genai

from .llm_utils import LLMUtils, AgentCollaborator

logger = logging.getLogger(__name__)


class DynamicWorkflowGenerator:
    """Generates dynamic, personalized onboarding workflows using LLM analysis."""
    
    def __init__(self, model: genai.GenerativeModel, collaborator: AgentCollaborator):
        """
        Initialize the DynamicWorkflowGenerator.
        
        Args:
            model: Configured Gemini GenerativeModel instance
            collaborator: AgentCollaborator instance for sharing insights
        """
        self.model = model
        self.llm_utils = LLMUtils(model)
        self.collaborator = collaborator
    
    def generate_personalized_workflow(
        self, 
        new_hire_data: Dict[str, str], 
        company_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a personalized onboarding workflow based on comprehensive analysis.
        
        Args:
            new_hire_data: Dictionary containing new hire information
            company_context: Optional company-specific context and policies
            
        Returns:
            Dict[str, Any]: Personalized workflow with phases, tasks, and timelines
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            logger.info(f"Generating personalized workflow for {full_name}")
            
            # Gather insights from all agents
            all_insights = self._gather_comprehensive_insights()
            
            # Generate workflow schema
            workflow_schema = {
                "workflow_overview": "object",
                "pre_boarding_phase": "object",
                "day1_phase": "object", 
                "first_week_phase": "object",
                "integration_phase": "object",
                "success_metrics": "array",
                "risk_assessment": "object",
                "customization_rationale": "array"
            }
            
            prompt = f"""
            Create a comprehensive, personalized onboarding workflow for a new employee with this profile:
            
            Employee Details:
            - Name: {full_name}
            - Job Title: {new_hire_data.get('job_title', 'Employee')}
            - Department: {new_hire_data.get('department', 'General')}
            - Start Date: {new_hire_data.get('start_date', 'TBD')}
            - Experience Level: {new_hire_data.get('experience_level', 'Mid-level')}
            - Manager: {new_hire_data.get('manager_name', 'Manager')}
            
            Company Context: {company_context or 'Standard tech company'}
            
            Agent Insights: {all_insights}
            
            Design a workflow that:
            1. Adapts to the specific role and experience level
            2. Incorporates insights from all onboarding agents
            3. Balances speed with thoroughness
            4. Includes measurable success metrics
            5. Identifies and mitigates potential risks
            6. Provides clear rationale for each customization
            
            For each phase, specify:
            - Key objectives and outcomes
            - Specific tasks and deliverables
            - Timeline and dependencies
            - Success criteria
            - Risk mitigation strategies
            """
            
            structured_response = self.llm_utils.generate_structured_response(
                prompt, workflow_schema, all_insights
            )
            
            if structured_response['success']:
                workflow_data = structured_response['data']
                
                # Enhance workflow with dynamic scheduling
                enhanced_workflow = self._enhance_workflow_with_scheduling(
                    workflow_data, new_hire_data
                )
                
                # Generate risk mitigation strategies
                risk_mitigation = self._generate_risk_mitigation_strategies(
                    enhanced_workflow, new_hire_data
                )
                
                # Share workflow insights with agents
                self._share_workflow_insights(enhanced_workflow, new_hire_data)
                
                logger.info(f"Generated personalized workflow for {full_name}")
                return {
                    'success': True,
                    'workflow': enhanced_workflow,
                    'risk_mitigation': risk_mitigation,
                    'customization_rationale': workflow_data.get('customization_rationale', []),
                    'generated_at': datetime.now().isoformat()
                }
            else:
                logger.warning(f"Failed to generate structured workflow: {structured_response['error']}")
                return self._get_fallback_workflow(new_hire_data)
                
        except Exception as e:
            logger.error(f"Workflow generation failed: {e}")
            return self._get_fallback_workflow(new_hire_data)
    
    def generate_adaptive_schedule(
        self, 
        workflow: Dict[str, Any], 
        new_hire_data: Dict[str, str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an adaptive schedule that adjusts based on progress and constraints.
        
        Args:
            workflow: The personalized workflow
            new_hire_data: Dictionary containing new hire information
            constraints: Optional scheduling constraints (availability, deadlines, etc.)
            
        Returns:
            Dict[str, Any]: Adaptive schedule with flexibility built-in
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            start_date = new_hire_data.get('start_date', '2023-10-27')
            
            schedule_schema = {
                "daily_schedules": "array",
                "milestone_dates": "array",
                "buffer_time": "object",
                "flexibility_options": "array",
                "contingency_plans": "array"
            }
            
            prompt = f"""
            Create an adaptive schedule for {full_name} starting {start_date} based on this workflow:
            
            Workflow: {workflow}
            Constraints: {constraints or 'Standard business hours, no major conflicts'}
            
            Design a schedule that:
            1. Optimizes learning and productivity
            2. Includes buffer time for unexpected delays
            3. Provides flexibility for different learning paces
            4. Accounts for dependencies between tasks
            5. Includes contingency plans for common issues
            6. Balances structured activities with unstructured time
            
            For each day, specify:
            - Primary activities and objectives
            - Time allocations and priorities
            - Dependencies and prerequisites
            - Success indicators
            - Alternative activities if primary ones fail
            """
            
            structured_response = self.llm_utils.generate_structured_response(
                prompt, schedule_schema
            )
            
            if structured_response['success']:
                schedule_data = structured_response['data']
                
                # Optimize schedule based on insights
                optimized_schedule = self._optimize_schedule_with_insights(
                    schedule_data, new_hire_data
                )
                
                logger.info(f"Generated adaptive schedule for {full_name}")
                return {
                    'success': True,
                    'schedule': optimized_schedule,
                    'generated_at': datetime.now().isoformat()
                }
            else:
                logger.warning(f"Failed to generate structured schedule: {structured_response['error']}")
                return self._get_fallback_schedule(new_hire_data)
                
        except Exception as e:
            logger.error(f"Schedule generation failed: {e}")
            return self._get_fallback_schedule(new_hire_data)
    
    def generate_progress_tracking_system(
        self, 
        workflow: Dict[str, Any], 
        new_hire_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive progress tracking system.
        
        Args:
            workflow: The personalized workflow
            new_hire_data: Dictionary containing new hire information
            
        Returns:
            Dict[str, Any]: Progress tracking system with metrics and checkpoints
        """
        try:
            full_name = new_hire_data.get('full_name', 'New Hire')
            
            tracking_schema = {
                "key_performance_indicators": "array",
                "checkpoint_schedule": "array",
                "progress_milestones": "array",
                "feedback_mechanisms": "array",
                "adjustment_triggers": "array"
            }
            
            prompt = f"""
            Create a comprehensive progress tracking system for {full_name} based on this workflow:
            
            Workflow: {workflow}
            
            Design a tracking system that:
            1. Measures both objective and subjective progress
            2. Includes regular checkpoints and feedback loops
            3. Identifies early warning signs of issues
            4. Provides actionable insights for improvements
            5. Enables data-driven workflow adjustments
            
            Include:
            - Quantifiable KPIs and success metrics
            - Regular checkpoint schedule with specific questions
            - Progress milestones with clear success criteria
            - Multiple feedback mechanisms (self, peer, manager)
            - Triggers for workflow adjustments or interventions
            """
            
            structured_response = self.llm_utils.generate_structured_response(
                prompt, tracking_schema
            )
            
            if structured_response['success']:
                tracking_data = structured_response['data']
                logger.info(f"Generated progress tracking system for {full_name}")
                return {
                    'success': True,
                    'tracking_system': tracking_data,
                    'generated_at': datetime.now().isoformat()
                }
            else:
                logger.warning(f"Failed to generate structured tracking system: {structured_response['error']}")
                return self._get_fallback_tracking_system(new_hire_data)
                
        except Exception as e:
            logger.error(f"Progress tracking generation failed: {e}")
            return self._get_fallback_tracking_system(new_hire_data)
    
    def _gather_comprehensive_insights(self) -> Dict[str, Any]:
        """Gather insights from all agents for workflow generation."""
        insights = {}
        
        # Get insights for each agent type
        agent_types = [
            'training_agent', 'buddy_agent', 'it_provisioning_agent',
            'scheduler_agent', 'integration_planner_agent'
        ]
        
        for agent_type in agent_types:
            agent_insights = self.collaborator.get_insights_for_agent(agent_type)
            if agent_insights:
                insights[agent_type] = agent_insights
        
        return insights
    
    def _enhance_workflow_with_scheduling(
        self, 
        workflow_data: Dict[str, Any], 
        new_hire_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """Enhance workflow with detailed scheduling and dependencies."""
        
        # Add timeline calculations
        start_date = datetime.strptime(
            new_hire_data.get('start_date', '2023-10-27'), 
            '%Y-%m-%d'
        )
        
        enhanced_workflow = workflow_data.copy()
        
        # Calculate phase timelines
        phase_timelines = {
            'pre_boarding': 7,  # days
            'day1': 1,
            'first_week': 7,
            'integration': 90
        }
        
        current_date = start_date
        for phase, duration in phase_timelines.items():
            if phase in enhanced_workflow:
                enhanced_workflow[phase]['start_date'] = current_date.isoformat()
                enhanced_workflow[phase]['end_date'] = (current_date + timedelta(days=duration)).isoformat()
                current_date += timedelta(days=duration)
        
        return enhanced_workflow
    
    def _generate_risk_mitigation_strategies(
        self, 
        workflow: Dict[str, Any], 
        new_hire_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """Generate risk mitigation strategies for the workflow."""
        
        try:
            risk_schema = {
                "identified_risks": "array",
                "mitigation_strategies": "array",
                "early_warning_indicators": "array",
                "contingency_plans": "array"
            }
            
            prompt = f"""
            Identify potential risks and mitigation strategies for this onboarding workflow:
            
            Workflow: {workflow}
            Employee: {new_hire_data.get('full_name', 'New Hire')} - {new_hire_data.get('job_title', 'Employee')}
            
            Consider risks related to:
            1. Learning pace and comprehension
            2. Technical setup and access issues
            3. Relationship building and team integration
            4. Workload management and overwhelm
            5. Manager availability and support
            6. External factors and dependencies
            
            For each risk, provide specific mitigation strategies and early warning indicators.
            """
            
            structured_response = self.llm_utils.generate_structured_response(
                prompt, risk_schema
            )
            
            if structured_response['success']:
                return structured_response['data']
            else:
                return self._get_fallback_risk_mitigation()
                
        except Exception as e:
            logger.error(f"Risk mitigation generation failed: {e}")
            return self._get_fallback_risk_mitigation()
    
    def _share_workflow_insights(
        self, 
        workflow: Dict[str, Any], 
        new_hire_data: Dict[str, str]
    ) -> None:
        """Share workflow insights with other agents."""
        
        self.collaborator.share_insight(
            'workflow_generator',
            'personalized_workflow',
            {
                'workflow_overview': workflow.get('workflow_overview', {}),
                'phase_timelines': {
                    phase: {
                        'start_date': phase_data.get('start_date'),
                        'end_date': phase_data.get('end_date')
                    }
                    for phase, phase_data in workflow.items()
                    if isinstance(phase_data, dict) and 'start_date' in phase_data
                },
                'success_metrics': workflow.get('success_metrics', []),
                'customization_rationale': workflow.get('customization_rationale', [])
            }
        )
    
    def _optimize_schedule_with_insights(
        self, 
        schedule_data: Dict[str, Any], 
        new_hire_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """Optimize schedule based on agent insights."""
        
        # Get relevant insights
        insights = self.collaborator.get_insights_for_agent('scheduler_agent')
        
        # Apply optimizations based on insights
        optimized_schedule = schedule_data.copy()
        
        # Add buffer time based on role complexity
        job_title = new_hire_data.get('job_title', 'Employee')
        if 'senior' in job_title.lower() or 'lead' in job_title.lower():
            # Senior roles need more time for complex tasks
            for day_schedule in optimized_schedule.get('daily_schedules', []):
                if 'buffer_time' in day_schedule:
                    day_schedule['buffer_time'] = int(day_schedule['buffer_time']) * 1.5
        
        return optimized_schedule
    
    def _get_fallback_workflow(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """Get a fallback workflow when generation fails."""
        
        return {
            'success': False,
            'workflow': {
                'workflow_overview': {
                    'total_duration_days': 30,
                    'approach': 'Standard onboarding process'
                },
                'pre_boarding_phase': {
                    'duration_days': 7,
                    'key_activities': ['Paperwork completion', 'Welcome kit', 'System access']
                },
                'day1_phase': {
                    'duration_days': 1,
                    'key_activities': ['Orientation', 'Manager meeting', 'Team introduction']
                },
                'first_week_phase': {
                    'duration_days': 7,
                    'key_activities': ['Training', 'Buddy assignment', 'Project setup']
                },
                'integration_phase': {
                    'duration_days': 90,
                    'key_activities': ['Project work', 'Performance reviews', 'Goal setting']
                }
            },
            'risk_mitigation': self._get_fallback_risk_mitigation(),
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_fallback_schedule(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """Get a fallback schedule when generation fails."""
        
        return {
            'success': False,
            'schedule': {
                'daily_schedules': [
                    {'day': 1, 'activities': ['Orientation', 'Manager meeting']},
                    {'day': 2, 'activities': ['Training', 'Team introduction']}
                ],
                'milestone_dates': ['Week 1', 'Week 4', 'Week 12'],
                'flexibility_options': ['Adjust training pace', 'Reschedule meetings']
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_fallback_tracking_system(self, new_hire_data: Dict[str, str]) -> Dict[str, Any]:
        """Get a fallback tracking system when generation fails."""
        
        return {
            'success': False,
            'tracking_system': {
                'key_performance_indicators': ['Task completion', 'Training progress', 'Team integration'],
                'checkpoint_schedule': ['Week 1', 'Week 4', 'Week 12'],
                'progress_milestones': ['Orientation complete', 'Training complete', 'First project complete']
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_fallback_risk_mitigation(self) -> Dict[str, Any]:
        """Get fallback risk mitigation strategies."""
        
        return {
            'identified_risks': [
                {'risk': 'Training delays', 'probability': 'Medium', 'impact': 'Low'},
                {'risk': 'System access issues', 'probability': 'Low', 'impact': 'Medium'}
            ],
            'mitigation_strategies': [
                {'risk': 'Training delays', 'strategy': 'Provide alternative learning resources'},
                {'risk': 'System access issues', 'strategy': 'IT support escalation process'}
            ],
            'early_warning_indicators': ['Missed deadlines', 'Low engagement scores'],
            'contingency_plans': ['Extended timeline', 'Additional support resources']
        }
