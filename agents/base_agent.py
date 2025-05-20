import json
import os
import uuid
import aiohttp  # Add this import for HTTP requests
from typing import Dict, Any, List, Optional
import abc
import sys
import os

# Add the project root to the path to enable absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_integration import AIIntegration

class BaseAgent(abc.ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, agent_id: str = None, name: str = "BaseAgent"):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.ai = AIIntegration()
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get basic information about this agent."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.__class__.__name__
        }
    
    @abc.abstractmethod
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a task assigned to this agent."""
        pass
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message sent to this agent."""
        content = message.get("content", {})
        return await self.handle_task(content)
    
    async def generate_ai_response(self, prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Generate a response using AI."""
        return await self.ai.generate_content(prompt, temperature)
    
    async def generate_json_response(self, prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Generate a JSON response from the AI."""
        try:
            # Use the existing AIIntegration class
            ai_response = await self.ai.generate_content(prompt, temperature)
            
            if ai_response["status"] != "success":
                return {
                    "status": "error",
                    "message": ai_response.get("message", "Unknown error generating content"),
                    "details": ai_response.get("details", {})
                }
            
            content = ai_response.get("content", "")
            
            # Try to parse the content as JSON
            try:
                # Find JSON content within the response (it might be wrapped in markdown code blocks)
                json_content = content
                if "```json" in content:
                    json_content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_content = content.split("```")[1].split("```")[0].strip()
                
                # Parse the JSON content
                data = json.loads(json_content)
                
                return {
                    "status": "success",
                    "message": "Successfully generated JSON response",
                    "data": data
                }
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract JSON using a more robust method
                try:
                    data = self.ai.extract_json_from_text(content)
                    if "raw_text" not in data:
                        return {
                            "status": "success",
                            "message": "Successfully extracted JSON response",
                            "data": data
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Failed to parse JSON response: {str(e)}",
                            "raw_content": content
                        }
                except Exception as json_ex:
                    return {
                        "status": "error",
                        "message": f"Failed to parse JSON response: {str(e)}, extraction error: {str(json_ex)}",
                        "raw_content": content
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error generating response: {str(e)}"
            }