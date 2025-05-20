from typing import Dict, Any, List
import json
from .base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """Agent responsible for breaking down tasks into actionable steps."""
    
    def __init__(self, agent_id: str = None, name: str = "PlannerAgent"):
        super().__init__(agent_id, name)
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message sent to this agent."""
        content = message.get("content", {})
        message_type = content.get("type", "")
        
        if message_type == "plan_goal":
            return await self._handle_plan_goal(content)
        elif message_type == "execute_step":
            return await self._handle_execute_step(content)
        else:
            return {
                "status": "error",
                "message": f"Unsupported task type: {message_type}",
                "task": content
            }

    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Break down a task into subtasks."""
        task_type = task.get("type", "")
        
        if task_type == "plan_goal":
            return await self._handle_plan_goal(task)
        elif task_type == "refine_plan":
            return await self._refine_plan(task)
        
        return {
            "status": "error",
            "message": f"Unsupported task type: {task_type}",
            "task": task
        }
    
    async def _handle_plan_goal(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a goal using AI."""
        goal = content.get("goal", "")
        
        if not goal:
            return {
                "status": "error",
                "message": "No goal provided for planning"
            }
        
        # Create a prompt for the AI with clear instructions to focus on the specific goal
        prompt = f"""
        You are an expert project planner. Please create a detailed plan for the following goal:
        
        Goal: {goal}
        
        IMPORTANT: Your plan must be specifically tailored to this exact goal. Do not create a generic plan or a plan for a different project.
        
        For example, if the goal is about a weather app, create a plan specifically for a weather app, not for a calculator or any other application.
        
        Your plan should include:
        1. A clear title that reflects the exact goal
        2. A series of steps with:
           - Step ID
           - Title
           - Description (specific to the goal)
           - Assigned role (architect_agent, coder_agent, etc.)
           - Dependencies (which steps must be completed first)
        
        Format your response as JSON with the following structure:
        {{
            "title": "Plan for: {goal}",
            "steps": [
                {{
                    "id": "step_1",
                    "title": "string",
                    "description": "string",
                    "assigned_to": "string",
                    "depends_on": ["string"] // Optional
                }}
            ]
        }}
        
        Ensure that each step is directly relevant to building {goal.split(':')[0] if ':' in goal else goal}.
        """
        
        # Call the AI to generate a response
        ai_response = await self.generate_json_response(prompt, temperature=0.2)  # Lower temperature for more focused output
        
        if ai_response["status"] == "success":
            # Validate that the plan is relevant to the goal
            plan_data = ai_response["data"]
            
            # Basic validation to ensure the plan is relevant
            goal_keywords = self._extract_keywords(goal.lower())
            plan_title = plan_data.get("title", "").lower()
            
            is_relevant = any(keyword in plan_title for keyword in goal_keywords)
            
            if is_relevant:
                return {
                    "status": "success",
                    "message": "Goal successfully planned by AI",
                    "plan": plan_data
                }
            else:
                # If the plan doesn't seem relevant, try again with more explicit instructions
                return await self._retry_plan_generation(goal)
        else:
            # Fall back to a manually created plan
            return self._create_fallback_plan(goal)
    
    async def _retry_plan_generation(self, goal: str) -> Dict[str, Any]:
        """Retry plan generation with more explicit instructions."""
        prompt = f"""
        You are an expert project planner. You MUST create a plan SPECIFICALLY for this goal:
        
        Goal: {goal}
        
        CRITICAL: Your plan must be about {goal.split(':')[0] if ':' in goal else goal} and nothing else.
        
        Your plan should include:
        1. A title that explicitly mentions {goal.split(':')[0] if ':' in goal else goal}
        2. Steps that are directly related to building {goal.split(':')[0] if ':' in goal else goal}
        
        Format your response as JSON with the following structure:
        {{
            "title": "Plan for: {goal}",
            "steps": [
                {{
                    "id": "step_1",
                    "title": "string",
                    "description": "string",
                    "assigned_to": "string",
                    "depends_on": ["string"] // Optional
                }}
            ]
        }}
        """
        
        ai_response = await self.generate_json_response(prompt, temperature=0.1)  # Even lower temperature
        
        if ai_response["status"] == "success":
            return {
                "status": "success",
                "message": "Goal successfully planned by AI (retry)",
                "plan": ai_response["data"]
            }
        else:
            return self._create_fallback_plan(goal)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key words from text for relevance checking."""
        # Remove common words and keep important keywords
        common_words = {"a", "an", "the", "and", "or", "but", "for", "with", "about", "create", "build", "develop", "implement"}
        words = text.split()
        return [word for word in words if word.lower() not in common_words and len(word) > 3]
    
    def _create_fallback_plan(self, goal: str) -> Dict[str, Any]:
        """Create a fallback plan when AI generation fails."""
        goal_type = goal.split(':')[0].strip().lower() if ':' in goal else goal.lower()
        
        if "weather" in goal_type:
            return {
                "status": "success",
                "message": "Goal successfully planned (fallback)",
                "plan": {
                    "title": f"Plan for: {goal}",
                    "steps": [
                        {
                            "id": "step_1",
                            "title": "Analyze weather app requirements",
                            "description": "Define the requirements for the weather application",
                            "assigned_to": "architect_agent"
                        },
                        {
                            "id": "step_2",
                            "title": "Design weather app architecture",
                            "description": "Create the architecture for the weather application",
                            "assigned_to": "architect_agent",
                            "depends_on": ["step_1"]
                        },
                        {
                            "id": "step_3",
                            "title": "Implement weather API integration",
                            "description": "Implement the integration with a weather data API",
                            "assigned_to": "coder_agent",
                            "depends_on": ["step_2"]
                        },
                        {
                            "id": "step_4",
                            "title": "Develop user interface",
                            "description": "Create the user interface for the weather app",
                            "assigned_to": "coder_agent",
                            "depends_on": ["step_2"]
                        },
                        {
                            "id": "step_5",
                            "title": "Implement forecast functionality",
                            "description": "Add the 5-day forecast feature",
                            "assigned_to": "coder_agent",
                            "depends_on": ["step_3", "step_4"]
                        },
                        {
                            "id": "step_6",
                            "title": "Test the application",
                            "description": "Test the weather application for bugs and issues",
                            "assigned_to": "coder_agent",
                            "depends_on": ["step_5"]
                        }
                    ]
                }
            }
        else:
            # Generic plan structure
            return {
                "status": "success",
                "message": "Goal successfully planned (fallback)",
                "plan": {
                    "title": f"Plan for: {goal}",
                    "steps": [
                        {
                            "id": "step_1",
                            "title": "Analyze requirements",
                            "description": f"Define the requirements for {goal_type}",
                            "assigned_to": "architect_agent"
                        },
                        {
                            "id": "step_2",
                            "title": "Design solution",
                            "description": f"Create the architecture for {goal_type}",
                            "assigned_to": "architect_agent",
                            "depends_on": ["step_1"]
                        },
                        {
                            "id": "step_3",
                            "title": "Implement solution",
                            "description": f"Implement {goal_type}",
                            "assigned_to": "coder_agent",
                            "depends_on": ["step_2"]
                        },
                        {
                            "id": "step_4",
                            "title": "Test solution",
                            "description": f"Test {goal_type}",
                            "assigned_to": "coder_agent",
                            "depends_on": ["step_3"]
                        }
                    ]
                }
            }
    
    # Other methods remain the same...