"""
LLM Utilities for the Onboarder system.

Provides enhanced LLM interaction capabilities including structured output parsing,
agent collaboration, and intelligent error recovery.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Per-request timeout for every Gemini call. Agents run in worker threads, where
# signal-based timeouts are unavailable, so the SDK's own timeout is used instead.
LLM_TIMEOUT_SECONDS = int(os.getenv("ONBOARDER_LLM_TIMEOUT", "30"))
LLM_REQUEST_OPTIONS = {"timeout": LLM_TIMEOUT_SECONDS}


class LLMUtils:
    """Utility class for enhanced LLM interactions with structured outputs."""
    
    def __init__(self, model: genai.GenerativeModel):
        """
        Initialize LLMUtils with a Gemini model.
        
        Args:
            model: Configured Gemini GenerativeModel instance
        """
        self.model = model
        self.conversation_history = []
    
    def generate_structured_response(
        self, 
        prompt: str, 
        expected_schema: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        timeout_seconds: int = LLM_TIMEOUT_SECONDS
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            expected_schema: Expected JSON schema for the response
            context: Additional context from other agents
            max_retries: Maximum number of retry attempts
            timeout_seconds: Per-request timeout passed to the Gemini SDK
            
        Returns:
            Dict[str, Any]: Parsed JSON response or error information
        """
        try:
            # Enhance prompt with schema requirements
            enhanced_prompt = self._build_structured_prompt(prompt, expected_schema, context)
            
            for attempt in range(max_retries):
                try:
                    # Use the SDK's per-request timeout. signal.alarm() cannot be used
                    # here because agents run in worker threads, not the main thread.
                    response = self.model.generate_content(
                        enhanced_prompt,
                        request_options={"timeout": timeout_seconds}
                    )
                    
                    if not response.text:
                        logger.warning(f"Empty response from LLM on attempt {attempt + 1}")
                        continue
                    
                    # Try to parse JSON response
                    parsed_response = self._parse_json_response(response.text)
                    
                    # Validate against expected schema
                    if self._validate_schema(parsed_response, expected_schema):
                        logger.info(f"Successfully generated structured response on attempt {attempt + 1}")
                        return {
                            'success': True,
                            'data': parsed_response,
                            'raw_response': response.text,
                            'attempts': attempt + 1
                        }
                    else:
                        logger.warning(f"Schema validation failed on attempt {attempt + 1}")
                        
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
            
            # If all attempts failed, return error
            return {
                'success': False,
                'error': 'Failed to generate valid structured response after all attempts',
                'raw_response': response.text if 'response' in locals() else None,
                'attempts': max_retries
            }
            
        except Exception as e:
            logger.error(f"Structured response generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'attempts': 0
            }
    
    def generate_with_context(
        self, 
        prompt: str, 
        agent_insights: Optional[Dict[str, Any]] = None,
        previous_responses: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response with context from other agents.
        
        Args:
            prompt: The main prompt
            agent_insights: Insights from other agents
            previous_responses: Previous LLM responses for context
            
        Returns:
            Dict[str, Any]: Generated response with metadata
        """
        try:
            # Build context-enhanced prompt
            context_prompt = self._build_context_prompt(prompt, agent_insights, previous_responses)
            
            response = self.model.generate_content(context_prompt, request_options=LLM_REQUEST_OPTIONS)
            
            return {
                'success': True,
                'response': response.text,
                'context_used': bool(agent_insights or previous_responses),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Context-aware generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_error_recovery_strategy(
        self, 
        error_context: Dict[str, Any],
        failed_operation: str,
        available_resources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate intelligent error recovery strategies.
        
        Args:
            error_context: Context about what went wrong
            failed_operation: The operation that failed
            available_resources: Available resources for recovery
            
        Returns:
            Dict[str, Any]: Recovery strategy and recommendations
        """
        try:
            prompt = f"""
            An error occurred during the onboarding process. Please provide a recovery strategy.
            
            Error Context: {error_context}
            Failed Operation: {failed_operation}
            Available Resources: {available_resources or 'Standard onboarding resources'}
            
            Provide a JSON response with:
            {{
                "recovery_strategy": "Primary recovery approach",
                "alternative_approaches": ["Alternative 1", "Alternative 2"],
                "immediate_actions": ["Action 1", "Action 2"],
                "long_term_fixes": ["Fix 1", "Fix 2"],
                "risk_assessment": "Low/Medium/High",
                "estimated_resolution_time": "Time estimate",
                "requires_human_intervention": true/false
            }}
            """
            
            response = self.model.generate_content(prompt, request_options=LLM_REQUEST_OPTIONS)
            parsed_response = self._parse_json_response(response.text)
            
            return {
                'success': True,
                'recovery_strategy': parsed_response,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error recovery strategy generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_strategy': {
                    'recovery_strategy': 'Manual intervention required',
                    'immediate_actions': ['Contact HR team', 'Log error for review'],
                    'risk_assessment': 'Medium',
                    'requires_human_intervention': True
                }
            }
    
    def _build_structured_prompt(
        self, 
        prompt: str, 
        schema: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build a prompt that enforces structured JSON output."""
        
        schema_example = self._create_schema_example(schema)
        
        enhanced_prompt = f"""
        {prompt}
        
        IMPORTANT: You must respond with valid JSON that matches this exact structure:
        
        {json.dumps(schema_example, indent=2)}
        
        The response must be valid JSON only, with no additional text or explanation.
        """
        
        if context:
            enhanced_prompt += f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        return enhanced_prompt
    
    def _build_context_prompt(
        self, 
        prompt: str, 
        agent_insights: Optional[Dict[str, Any]] = None,
        previous_responses: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build a prompt enhanced with context from other agents."""
        
        context_prompt = prompt
        
        if agent_insights:
            context_prompt += f"\n\nInsights from other agents:\n"
            for agent, insight in agent_insights.items():
                context_prompt += f"- {agent}: {insight}\n"
        
        if previous_responses:
            context_prompt += f"\n\nPrevious LLM responses for context:\n"
            for i, response in enumerate(previous_responses[-3:]):  # Last 3 responses
                context_prompt += f"Response {i+1}: {response.get('response', response.get('data', 'N/A'))}\n"
        
        return context_prompt
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling common formatting issues."""
        
        # Clean the response text
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        # Try to find JSON object in the response
        start_idx = cleaned_text.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object found in response")
        
        # Find the matching closing brace
        brace_count = 0
        end_idx = start_idx
        for i, char in enumerate(cleaned_text[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        json_text = cleaned_text[start_idx:end_idx]
        
        # Clean up common JSON formatting issues
        json_text = self._clean_json_text(json_text)
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Attempted to parse: {json_text}")
            raise
    
    def _clean_json_text(self, json_text: str) -> str:
        """Clean JSON text to handle common LLM formatting issues."""
        import re
        
        # Remove trailing commas before closing braces and brackets
        # This regex matches comma followed by optional whitespace and closing brace/bracket
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Remove trailing commas in object properties
        # This handles cases like: "key": "value",} -> "key": "value"}
        json_text = re.sub(r',(\s*})', r'\1', json_text)
        
        # Remove trailing commas in array elements
        # This handles cases like: "item",] -> "item"]
        json_text = re.sub(r',(\s*\])', r'\1', json_text)
        
        # Fix any double commas that might have been created
        json_text = re.sub(r',,', ',', json_text)
        
        # Remove any trailing commas at the end of the string
        json_text = re.sub(r',(\s*)$', r'\1', json_text)
        
        return json_text
    
    def _create_schema_example(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create an example object based on the schema."""
        
        example = {}
        for key, value_type in schema.items():
            if isinstance(value_type, dict):
                example[key] = self._create_schema_example(value_type)
            elif value_type == "string":
                example[key] = "example_string"
            elif value_type == "number":
                example[key] = 123
            elif value_type == "boolean":
                example[key] = True
            elif value_type == "array":
                example[key] = ["item1", "item2"]
            else:
                example[key] = f"example_{value_type}"
        
        return example
    
    def _validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate data against expected schema."""
        
        try:
            for key, expected_type in schema.items():
                if key not in data:
                    logger.warning(f"Missing required key: {key}")
                    return False
                
                actual_value = data[key]
                
                if isinstance(expected_type, dict):
                    if not isinstance(actual_value, dict):
                        logger.warning(f"Expected dict for {key}, got {type(actual_value)}")
                        return False
                    if not self._validate_schema(actual_value, expected_type):
                        return False
                elif expected_type == "array":
                    if not isinstance(actual_value, list):
                        logger.warning(f"Expected array for {key}, got {type(actual_value)}")
                        return False
                elif expected_type == "string":
                    if not isinstance(actual_value, str):
                        logger.warning(f"Expected string for {key}, got {type(actual_value)}")
                        return False
                elif expected_type == "number":
                    if not isinstance(actual_value, (int, float)):
                        logger.warning(f"Expected number for {key}, got {type(actual_value)}")
                        return False
                elif expected_type == "boolean":
                    if not isinstance(actual_value, bool):
                        logger.warning(f"Expected boolean for {key}, got {type(actual_value)}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return False


class AgentCollaborator:
    """Facilitates collaboration between different agents."""
    
    def __init__(self):
        """Initialize the AgentCollaborator."""
        self.shared_insights = {}
        self.cross_agent_dependencies = {}
    
    def share_insight(
        self, 
        from_agent: str, 
        insight_type: str, 
        insight_data: Dict[str, Any]
    ) -> None:
        """
        Share insights between agents.
        
        Args:
            from_agent: Name of the agent sharing the insight
            insight_type: Type of insight (e.g., 'role_analysis', 'training_requirements')
            insight_data: The insight data
        """
        if from_agent not in self.shared_insights:
            self.shared_insights[from_agent] = {}
        
        self.shared_insights[from_agent][insight_type] = {
            'data': insight_data,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Insight shared from {from_agent}: {insight_type}")
    
    def get_insights_for_agent(self, target_agent: str) -> Dict[str, Any]:
        """
        Get relevant insights for a specific agent.
        
        Args:
            target_agent: Name of the agent requesting insights
            
        Returns:
            Dict[str, Any]: Relevant insights from other agents
        """
        relevant_insights = {}
        
        # Define which insights are relevant for which agents
        insight_mappings = {
            'training_agent': ['role_analysis', 'department_info', 'skill_assessment'],
            'buddy_agent': ['role_analysis', 'department_info', 'personality_traits'],
            'it_provisioning_agent': ['role_analysis', 'department_info', 'access_requirements'],
            'scheduler_agent': ['role_analysis', 'training_schedule', 'buddy_availability'],
            'integration_planner_agent': ['role_analysis', 'training_requirements', 'buddy_assignment']
        }
        
        required_insights = insight_mappings.get(target_agent, [])
        
        for agent, insights in self.shared_insights.items():
            for insight_type, insight_data in insights.items():
                if insight_type in required_insights:
                    relevant_insights[f"{agent}_{insight_type}"] = insight_data['data']
        
        return relevant_insights
    
    def register_dependency(
        self, 
        dependent_agent: str, 
        depends_on_agent: str, 
        dependency_type: str
    ) -> None:
        """
        Register a dependency between agents.
        
        Args:
            dependent_agent: Agent that depends on another
            depends_on_agent: Agent that the dependent agent relies on
            dependency_type: Type of dependency
        """
        if dependent_agent not in self.cross_agent_dependencies:
            self.cross_agent_dependencies[dependent_agent] = []
        
        self.cross_agent_dependencies[dependent_agent].append({
            'depends_on': depends_on_agent,
            'type': dependency_type,
            'registered_at': datetime.now().isoformat()
        })
        
        logger.info(f"Dependency registered: {dependent_agent} depends on {depends_on_agent}")
