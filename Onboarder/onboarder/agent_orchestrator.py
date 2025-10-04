#!/usr/bin/env python3
"""
Agent Orchestrator for the Onboarder system.

Manages the sequential execution of onboarding agents with proper context sharing
and state management through the FastAPI server.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from .welcome_agent import WelcomeAgent
from .paperwork_agent import PaperworkAgent
from .it_provisioning_agent import ITProvisioningAgent
from .scheduler_agent import SchedulerAgent
from .buddy_agent import BuddyAgent
from .training_agent import TrainingAgent
from .integration_planner_agent import IntegrationPlannerAgent
from .context_manager import ContextManager
from .tools.llm_utils import AgentCollaborator

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates the sequential execution of onboarding agents."""
    
    def __init__(self, db_manager):
        """Initialize the AgentOrchestrator."""
        self.db_manager = db_manager
        self.context_manager = ContextManager(db_manager)
        
        # Initialize agent collaborator
        self.collaborator = AgentCollaborator()
        
        # Initialize agents with proper dependencies
        self.agents = {
            'PRE_BOARDING': [
                WelcomeAgent(),
                PaperworkAgent()
            ],
            'DAY1_SETUP': [
                ITProvisioningAgent(self.collaborator)
            ],
            'INTEGRATION': [
                SchedulerAgent(),
                BuddyAgent(self.collaborator),
                TrainingAgent(self.collaborator),
                IntegrationPlannerAgent()
            ]
        }
        
        # Phase order
        self.phase_order = ['PRE_BOARDING', 'DAY1_SETUP', 'INTEGRATION']
        
        logger.info("AgentOrchestrator initialized")
    
    async def start_onboarding_process(self, employee_id: str, onboarding_id: str):
        """
        Start the complete onboarding process for an employee.
        
        Args:
            employee_id: Employee ID
            onboarding_id: Onboarding ID
        """
        try:
            logger.info(f"Starting onboarding process for employee {employee_id}")
            
            # Get current onboarding state
            record = self.db_manager.get_onboarding_record(onboarding_id)
            if not record:
                logger.error(f"Onboarding record not found: {onboarding_id}")
                return
            
            # Start from current phase
            current_phase = record.get('current_phase', 'PRE_BOARDING')
            completed_phases = record.get('completed_phases', [])
            
            # Execute phases sequentially with timeout handling
            for phase in self.phase_order:
                if phase in completed_phases:
                    logger.info(f"Phase {phase} already completed for {employee_id}")
                    continue
                
                if phase == current_phase or self._should_execute_phase(phase, completed_phases):
                    logger.info(f"Executing phase {phase} for {employee_id}")
                    
                    try:
                        # Execute phase with timeout
                        await asyncio.wait_for(
                            self._execute_phase_async(employee_id, onboarding_id, phase),
                            timeout=120  # 2 minutes timeout per phase
                        )
                        
                        # Check if phase completed successfully
                        updated_record = self.db_manager.get_onboarding_record(onboarding_id)
                        if not updated_record:
                            logger.error(f"Could not retrieve updated record for {employee_id}")
                            break
                        
                        # If phase failed, stop execution
                        if updated_record.get('status') == 'FAILED':
                            logger.error(f"Phase {phase} failed for {employee_id}, stopping execution")
                            break
                        
                        # If phase not in completed phases, it failed
                        if phase not in updated_record.get('completed_phases', []):
                            logger.error(f"Phase {phase} did not complete for {employee_id}, stopping execution")
                            break
                            
                    except asyncio.TimeoutError:
                        logger.error(f"Phase {phase} timed out for {employee_id}")
                        self.db_manager.update_onboarding_record(onboarding_id, {
                            'status': 'FAILED',
                            'errors': [f"Phase {phase} timed out after 2 minutes"]
                        })
                        break
                    except Exception as phase_error:
                        logger.error(f"Phase {phase} failed for {employee_id}: {phase_error}")
                        self.db_manager.update_onboarding_record(onboarding_id, {
                            'status': 'FAILED',
                            'errors': [f"Phase {phase} failed: {str(phase_error)}"]
                        })
                        break
            
            # Check if all phases are completed
            final_record = self.db_manager.get_onboarding_record(onboarding_id)
            if final_record and len(final_record.get('completed_phases', [])) == len(self.phase_order):
                self.db_manager.update_onboarding_record(onboarding_id, {
                    'status': 'COMPLETED',
                    'end_time': datetime.now().isoformat(),
                    'current_phase': 'COMPLETED'
                })
                logger.info(f"Onboarding completed for {employee_id}")
            
        except Exception as e:
            logger.error(f"Onboarding process failed for {employee_id}: {e}")
            self.db_manager.update_onboarding_record(onboarding_id, {
                'status': 'FAILED',
                'errors': [str(e)]
            })
    
    async def _execute_phase_async(self, employee_id: str, onboarding_id: str, phase: str):
        """
        Execute a specific phase for an employee asynchronously.
        
        Args:
            employee_id: Employee ID
            onboarding_id: Onboarding ID
            phase: Phase to execute
        """
        # Run the synchronous execute_phase in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.execute_phase, employee_id, onboarding_id, phase)

    def execute_phase(self, employee_id: str, onboarding_id: str, phase: str):
        """
        Execute a specific phase for an employee.
        
        Args:
            employee_id: Employee ID
            onboarding_id: Onboarding ID
            phase: Phase to execute
        """
        try:
            logger.info(f"Executing phase {phase} for employee {employee_id}")
            
            # Get onboarding record
            record = self.db_manager.get_onboarding_record(onboarding_id)
            if not record:
                logger.error(f"Onboarding record not found: {onboarding_id}")
                return
            
            # Get context for this phase
            context = self.context_manager.get_phase_context(employee_id, phase)
            
            # Get agents for this phase
            phase_agents = self.agents.get(phase, [])
            if not phase_agents:
                logger.warning(f"No agents found for phase {phase}")
                return
            
            # Execute each agent in the phase
            phase_results = {}
            for agent in phase_agents:
                agent_name = agent.__class__.__name__
                logger.info(f"Executing {agent_name} for {employee_id}")
                
                try:
                    logger.info(f"Running agent {agent_name} with context: {bool(context)}")
                    
                    # Run agent with context
                    result = self._run_agent_with_context(
                        agent, record['new_hire_data'], context
                    )
                    
                    logger.info(f"Agent {agent_name} completed with status: {result.get('status', 'UNKNOWN')}")
                    phase_results[agent_name] = result
                    
                    # Log phase result
                    self.db_manager.add_phase_result(
                        onboarding_id, phase, agent_name, 
                        result.get('status', 'UNKNOWN'), result
                    )
                    
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed with exception: {e}", exc_info=True)
                    phase_results[agent_name] = {
                        'status': 'FAILED',
                        'error': str(e),
                        'exception_type': type(e).__name__
                    }
                    
                    # Log failed phase result
                    self.db_manager.add_phase_result(
                        onboarding_id, phase, agent_name, 
                        'FAILED', None, str(e)
                    )
            
            # Check if all agents in phase succeeded
            all_success = all(
                result.get('status') in ['SUCCESS', 'COMPLETED', 'AWAITING_SIGNATURE'] 
                for result in phase_results.values()
            )
            
            # Update onboarding record with phase results
            completed_phases = record.get('completed_phases', [])
            
            # Only add to completed phases if all agents succeeded
            if all_success and phase not in completed_phases:
                completed_phases.append(phase)
            
            # Update results
            current_results = record.get('results', {})
            current_results[phase.lower()] = phase_results
            
            # Determine next phase
            next_phase = self._get_next_phase(phase) if all_success else phase
            
            self.db_manager.update_onboarding_record(onboarding_id, {
                'current_phase': next_phase,
                'completed_phases': completed_phases,
                'results': current_results,
                'status': 'FAILED' if not all_success else 'IN_PROGRESS'
            })
            
            # Update context with phase results
            self.context_manager.update_phase_context(employee_id, phase, phase_results)
            
            logger.info(f"Phase {phase} completed for {employee_id} with success: {all_success}")
            
        except Exception as e:
            logger.error(f"Phase execution failed for {employee_id}, phase {phase}: {e}")
            self.db_manager.update_onboarding_record(onboarding_id, {
                'status': 'FAILED',
                'errors': [f"Phase {phase} failed: {str(e)}"]
            })
    
    def _run_agent_with_context(self, agent, new_hire_data: Dict[str, Any], context: Dict[str, Any]):
        """
        Run an agent with the provided context.
        
        Args:
            agent: The agent to run
            new_hire_data: New hire information
            context: Context information for the agent
            
        Returns:
            Dict[str, Any]: Agent execution result
        """
        try:
            # Create context-aware data
            context_aware_data = {
                **new_hire_data,
                'context': context
            }
            
            logger.info(f"Running agent {agent.__class__.__name__} with data keys: {list(context_aware_data.keys())}")
            
            # Run the agent
            if hasattr(agent, 'run'):
                result = agent.run(context_aware_data)
            elif hasattr(agent, 'execute'):
                result = agent.execute(context_aware_data)
            else:
                raise ValueError(f"Agent {agent.__class__.__name__} has no run or execute method")
            
            logger.info(f"Agent {agent.__class__.__name__} returned result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            return {
                'status': 'FAILED',
                'error': str(e),
                'exception_type': type(e).__name__
            }
    
    def _should_execute_phase(self, phase: str, completed_phases: List[str]) -> bool:
        """
        Determine if a phase should be executed based on completed phases.
        
        Args:
            phase: Phase to check
            completed_phases: List of completed phases
            
        Returns:
            bool: True if phase should be executed
        """
        phase_index = self.phase_order.index(phase)
        
        # If this is the first phase, execute it
        if phase_index == 0:
            return True
        
        # Check if all previous phases are completed
        previous_phases = self.phase_order[:phase_index]
        return all(prev_phase in completed_phases for prev_phase in previous_phases)
    
    def _get_next_phase(self, current_phase: str) -> Optional[str]:
        """
        Get the next phase in the sequence.
        
        Args:
            current_phase: Current phase
            
        Returns:
            str: Next phase or None if no next phase
        """
        try:
            current_index = self.phase_order.index(current_phase)
            next_index = current_index + 1
            
            if next_index < len(self.phase_order):
                return self.phase_order[next_index]
            else:
                return None
                
        except ValueError:
            logger.error(f"Invalid phase: {current_phase}")
            return None
    
    def get_agent_status(self, employee_id: str) -> Dict[str, Any]:
        """
        Get the current status of all agents for an employee.
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Dict[str, Any]: Agent status information
        """
        try:
            record = self.db_manager.get_onboarding_by_employee_id(employee_id)
            if not record:
                return {'error': 'Employee not found'}
            
            onboarding_id = record['onboarding_id']
            phase_results = self.db_manager.get_phase_results(onboarding_id)
            
            # Organize results by phase and agent
            organized_results = {}
            for result in phase_results:
                phase = result['phase']
                agent = result['agent']
                
                if phase not in organized_results:
                    organized_results[phase] = {}
                
                organized_results[phase][agent] = {
                    'status': result['status'],
                    'results': result.get('results'),
                    'error_message': result.get('error_message'),
                    'created_at': result['created_at']
                }
            
            return {
                'employee_id': employee_id,
                'current_phase': record['current_phase'],
                'completed_phases': record['completed_phases'],
                'phase_results': organized_results
            }
            
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {'error': str(e)}
