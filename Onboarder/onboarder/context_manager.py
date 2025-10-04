#!/usr/bin/env python3
"""
Context Manager for the Onboarder system.

Manages onboarding context and markdown templates for each phase,
ensuring agents receive only relevant information.
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages onboarding context and templates for each phase."""
    
    def __init__(self, db_manager):
        """Initialize the ContextManager."""
        self.db_manager = db_manager
        self.template_dir = Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
        # Initialize default templates
        self._initialize_default_templates()
        
        logger.info("ContextManager initialized")
    
    def _initialize_default_templates(self):
        """Initialize default markdown templates for each phase."""
        
        # Pre-boarding template
        pre_boarding_template = """# Pre-Boarding Phase - {full_name}

## Employee Information
- **Name**: {full_name}
- **Email**: {personal_email}
- **Job Title**: {job_title}
- **Manager**: {manager_name}
- **Start Date**: {start_date}

## Pre-Boarding Checklist
- [ ] Welcome email sent
- [ ] Welcome kit requested
- [ ] Employment contract prepared
- [ ] Personal information form prepared
- [ ] Background check initiated (if required)
- [ ] IT equipment ordered

## Context for Agents
- **Welcome Agent**: Send personalized welcome email and request welcome kit
- **Paperwork Agent**: Generate employment contract and personal info form

## Next Steps
- Complete paperwork collection
- Prepare for Day 1 setup
- Coordinate with IT for equipment setup
"""
        
        # Day 1 Setup template
        day1_template = """# Day 1 Setup Phase - {full_name}

## Employee Information
- **Name**: {full_name}
- **Email**: {personal_email}
- **Job Title**: {job_title}
- **Manager**: {manager_name}
- **Start Date**: {start_date}

## Day 1 Setup Checklist
- [ ] IT equipment configured
- [ ] User accounts created
- [ ] Software licenses assigned
- [ ] Access permissions granted
- [ ] Email account set up
- [ ] VPN access configured (if required)
- [ ] Phone system setup (if required)

## Context for Agents
- **IT Provisioning Agent**: Set up all technical equipment and accounts

## Previous Phase Results
{pre_boarding_results}

## Next Steps
- Complete IT setup
- Prepare for integration phase
- Schedule first week activities
"""
        
        # Integration template
        integration_template = """# Integration Phase - {full_name}

## Employee Information
- **Name**: {full_name}
- **Email**: {personal_email}
- **Job Title**: {job_title}
- **Manager**: {manager_name}
- **Start Date**: {start_date}

## Integration Checklist
- [ ] Schedule first week meetings
- [ ] Assign buddy/mentor
- [ ] Enroll in training programs
- [ ] Create integration plan
- [ ] Set up regular check-ins
- [ ] Plan team introductions
- [ ] Schedule performance review timeline

## Context for Agents
- **Scheduler Agent**: Create first week meeting schedule
- **Buddy Agent**: Assign appropriate buddy/mentor
- **Training Agent**: Enroll in relevant training programs
- **Integration Planner Agent**: Create comprehensive integration plan

## Previous Phase Results
{day1_results}

## Next Steps
- Complete all integration activities
- Begin regular check-ins
- Monitor progress and adjust plan as needed
"""
        
        # Save templates only if they don't exist
        if not (self.template_dir / "pre_boarding.md").exists():
            self._save_template("pre_boarding.md", pre_boarding_template)
        if not (self.template_dir / "day1_setup.md").exists():
            self._save_template("day1_setup.md", day1_template)
        if not (self.template_dir / "integration.md").exists():
            self._save_template("integration.md", integration_template)
        
        logger.info("Default templates initialized")
    
    def _save_template(self, filename: str, content: str):
        """Save a template to file."""
        template_path = self.template_dir / filename
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_phase_context(self, employee_id: str, phase: str) -> Dict[str, Any]:
        """
        Get context information for a specific phase.
        
        Args:
            employee_id: Employee ID
            phase: Phase name
            
        Returns:
            Dict[str, Any]: Context information for the phase
        """
        try:
            # Get onboarding record
            record = self.db_manager.get_onboarding_by_employee_id(employee_id)
            if not record:
                logger.error(f"Employee {employee_id} not found")
                return {}
            
            # Get stored context
            stored_context = record.get('onboarding_context', {})
            phase_context = stored_context.get(phase, {})
            
            # If no stored context, generate from template
            if not phase_context:
                phase_context = self._generate_context_from_template(employee_id, phase)
                self._store_phase_context(employee_id, phase, phase_context)
            
            return phase_context
            
        except Exception as e:
            logger.error(f"Error getting phase context: {e}")
            return {}
    
    def _generate_context_from_template(self, employee_id: str, phase: str) -> Dict[str, Any]:
        """
        Generate context from markdown template.
        
        Args:
            employee_id: Employee ID
            phase: Phase name
            
        Returns:
            Dict[str, Any]: Generated context
        """
        try:
            # Get onboarding record
            record = self.db_manager.get_onboarding_by_employee_id(employee_id)
            if not record:
                return {}
            
            new_hire_data = record['new_hire_data']
            
            # Load template
            template_path = self.template_dir / f"{phase.lower()}.md"
            if not template_path.exists():
                logger.warning(f"Template not found for phase {phase}")
                return {}
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Format template with employee data
            formatted_content = template_content.format(
                full_name=new_hire_data.get('full_name', 'Employee'),
                personal_email=new_hire_data.get('personal_email', ''),
                job_title=new_hire_data.get('job_title', ''),
                manager_name=new_hire_data.get('manager_name', ''),
                start_date=new_hire_data.get('start_date', ''),
                pre_boarding_results=self._format_previous_results(record, 'PRE_BOARDING'),
                day1_results=self._format_previous_results(record, 'DAY1_SETUP')
            )
            
            # Create context object
            context = {
                'template_content': formatted_content,
                'employee_data': new_hire_data,
                'phase': phase,
                'generated_at': datetime.now().isoformat(),
                'checklist_items': self._extract_checklist_items(formatted_content),
                'agent_instructions': self._extract_agent_instructions(formatted_content)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error generating context from template: {e}")
            return {}
    
    def _format_previous_results(self, record: Dict[str, Any], phase: str) -> str:
        """Format previous phase results for inclusion in context."""
        try:
            results = record.get('results', {})
            phase_results = results.get(phase.lower(), {})
            
            if not phase_results:
                return "No previous results available."
            
            formatted_results = []
            for agent_name, agent_result in phase_results.items():
                status = agent_result.get('status', 'UNKNOWN')
                formatted_results.append(f"- **{agent_name}**: {status}")
            
            return "\n".join(formatted_results) if formatted_results else "No results available."
            
        except Exception as e:
            logger.error(f"Error formatting previous results: {e}")
            return "Error formatting previous results."
    
    def _extract_checklist_items(self, content: str) -> List[Dict[str, Any]]:
        """Extract checklist items from markdown content."""
        checklist_items = []
        lines = content.split('\n')
        
        for line in lines:
            if line.strip().startswith('- [ ]'):
                item = line.strip()[4:].strip()  # Remove '- [ ]'
                checklist_items.append({
                    'item': item,
                    'completed': False
                })
            elif line.strip().startswith('- [x]'):
                item = line.strip()[4:].strip()  # Remove '- [x]'
                checklist_items.append({
                    'item': item,
                    'completed': True
                })
        
        return checklist_items
    
    def _extract_agent_instructions(self, content: str) -> Dict[str, str]:
        """Extract agent-specific instructions from content."""
        instructions = {}
        lines = content.split('\n')
        
        current_agent = None
        for line in lines:
            if '**' in line and 'Agent**' in line:
                # Extract agent name
                agent_line = line.strip()
                if ': ' in agent_line:
                    agent_name = agent_line.split(': ')[0].replace('**', '').replace('*', '')
                    instruction = agent_line.split(': ', 1)[1]
                    instructions[agent_name] = instruction
        
        return instructions
    
    def update_phase_context(self, employee_id: str, phase: str, phase_results: Dict[str, Any]):
        """
        Update context with phase results.
        
        Args:
            employee_id: Employee ID
            phase: Phase name
            phase_results: Results from phase execution
        """
        try:
            # Get current context
            record = self.db_manager.get_onboarding_by_employee_id(employee_id)
            if not record:
                return
            
            onboarding_context = record.get('onboarding_context', {})
            phase_context = onboarding_context.get(phase, {})
            
            # Update context with results
            phase_context['last_execution'] = {
                'timestamp': datetime.now().isoformat(),
                'results': phase_results
            }
            
            # Update checklist items based on results
            if 'checklist_items' in phase_context:
                checklist_items = phase_context['checklist_items']
                for item in checklist_items:
                    # Mark items as completed based on agent results
                    if self._should_mark_completed(item['item'], phase_results):
                        item['completed'] = True
                        item['completed_at'] = datetime.now().isoformat()
            
            # Store updated context
            onboarding_context[phase] = phase_context
            self.db_manager.update_onboarding_record(record['onboarding_id'], {
                'onboarding_context': onboarding_context
            })
            
        except Exception as e:
            logger.error(f"Error updating phase context: {e}")
    
    def _should_mark_completed(self, item: str, phase_results: Dict[str, Any]) -> bool:
        """Determine if a checklist item should be marked as completed."""
        item_lower = item.lower()
        
        # Check if any agent result indicates completion
        for agent_name, result in phase_results.items():
            if result.get('status') == 'SUCCESS':
                # Map agent results to checklist items
                if 'welcome' in item_lower and 'welcome' in agent_name.lower():
                    return True
                elif 'paperwork' in item_lower and 'paperwork' in agent_name.lower():
                    return True
                elif 'it' in item_lower and 'it' in agent_name.lower():
                    return True
                elif 'schedule' in item_lower and 'scheduler' in agent_name.lower():
                    return True
                elif 'buddy' in item_lower and 'buddy' in agent_name.lower():
                    return True
                elif 'training' in item_lower and 'training' in agent_name.lower():
                    return True
                elif 'integration' in item_lower and 'integration' in agent_name.lower():
                    return True
        
        return False
    
    def _store_phase_context(self, employee_id: str, phase: str, context: Dict[str, Any]):
        """Store phase context in the database."""
        try:
            record = self.db_manager.get_onboarding_by_employee_id(employee_id)
            if not record:
                return
            
            onboarding_context = record.get('onboarding_context', {})
            onboarding_context[phase] = context
            
            self.db_manager.update_onboarding_record(record['onboarding_id'], {
                'onboarding_context': onboarding_context
            })
            
        except Exception as e:
            logger.error(f"Error storing phase context: {e}")
    
    def get_context_summary(self, employee_id: str) -> Dict[str, Any]:
        """
        Get a summary of all context information for an employee.
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Dict[str, Any]: Context summary
        """
        try:
            record = self.db_manager.get_onboarding_by_employee_id(employee_id)
            if not record:
                return {'error': 'Employee not found'}
            
            context = record.get('onboarding_context', {})
            
            summary = {
                'employee_id': employee_id,
                'current_phase': record['current_phase'],
                'phases': {}
            }
            
            for phase, phase_context in context.items():
                summary['phases'][phase] = {
                    'has_context': bool(phase_context),
                    'last_updated': phase_context.get('generated_at'),
                    'checklist_items': len(phase_context.get('checklist_items', [])),
                    'completed_items': sum(1 for item in phase_context.get('checklist_items', []) if item.get('completed', False))
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting context summary: {e}")
            return {'error': str(e)}
