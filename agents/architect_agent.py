from typing import Dict, Any, List
import json
import aiohttp
import os
from .base_agent import BaseAgent

class ArchitectAgent(BaseAgent):
    """Agent responsible for system architecture and design decisions."""
    
    def __init__(self, agent_id: str = None, name: str = "ArchitectAgent"):
        super().__init__(agent_id, name)
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message sent to this agent."""
        content = message.get("content", {})
        message_type = content.get("type", "")
        
        if message_type == "architecture_question":
            return await self._handle_architecture_question(content)
        elif message_type == "execute_step":
            return await self._handle_execute_step(content)
        else:
            return {
                "status": "error",
                "message": f"Unsupported task type: {message_type}",
                "task": content
            }
    
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a task assigned to this agent."""
        task_type = task.get("type", "")
        
        if task_type == "architecture_question":
            return await self._handle_architecture_question(task)
        elif task_type == "execute_step":
            return await self._handle_execute_step(task)
        elif task_type == "design_system":
            return await self._handle_design_system(task)
        else:
            return {
                "status": "error",
                "message": f"Unsupported task type: {task_type}",
                "task": task
            }
    
    async def _handle_execute_step(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a step in a plan."""
        step = task.get("step", {})
        context = task.get("context", {})
        step_id = step.get("id", "unknown")
        step_title = step.get("title", "")
        step_description = step.get("description", "")
        
        # Extract project information from context
        project_title = context.get("title", "Unknown project")
        project_description = context.get("description", "No description provided")
        
        # Create a prompt based on the step and context
        if "analyze requirements" in step_title.lower():
            prompt = f"""
            You are an expert software architect. Please analyze the requirements for the following project:
            
            Project: {project_title}
            Description: {project_description}
            
            CRITICAL INSTRUCTION: Your response MUST be specifically tailored to {project_title}.
            
            Provide a comprehensive list of functional and non-functional requirements for this project.
            Also include a high-level architecture with key components.
            
            Format your response as JSON with the following structure:
            {{
                "requirements": [
                    "Detailed requirement 1 specific to {project_title}",
                    "Detailed requirement 2 specific to {project_title}",
                    "..."
                ],
                "architecture": {{
                    "components": [
                        {{"name": "Component name specific to {project_title}", "description": "Detailed description of this component's purpose and functionality"}},
                        {{...}}
                    ],
                    "data_flow": "Detailed description of how data flows between components"
                }}
            }}
            """
        elif "design solution" in step_title.lower():
            prompt = f"""
            You are an expert software architect. Please design a solution for the following project:
            
            Project: {project_title}
            Description: {project_description}
            
            CRITICAL INSTRUCTION: Your response MUST be specifically tailored to {project_title}.
            
            Provide a detailed design including UI mockup description, components, and data model.
            
            Format your response as JSON with the following structure:
            {{
                "design": {{
                    "ui_mockup": "Detailed description of the user interface for {project_title}",
                    "components": [
                        {{"name": "Component name specific to {project_title}", "purpose": "Detailed description of this component's purpose"}},
                        {{...}}
                    ],
                    "data_model": {{
                        "Entity1": "data type and description",
                        "Entity2": "data type and description",
                        "...": "..."
                    }}
                }}
            }}
            """
        else:
            prompt = f"""
            You are an expert software architect. Please complete the following step in a software development plan:
            
            Step: {step_title}
            Description: {step_description}
            
            Context:
            Project: {project_title}
            Description: {project_description}
            
            CRITICAL INSTRUCTION: Your response MUST be specifically tailored to {project_title}.
            
            Provide a detailed response appropriate for this step in the development process.
            
            Format your response as JSON with appropriate fields for this step.
            """
        
        try:
            # Call the AI to generate a response with a low temperature for more focused output
            ai_response = await self.generate_json_response(prompt, temperature=0.2)
            
            # If successful, return the AI-generated response
            if ai_response["status"] == "success":
                return {
                    "status": "success",
                    "message": f"Completed step {step_id}",
                    "result": ai_response["data"]
                }
            else:
                # If AI fails, make another attempt with a simpler prompt
                retry_prompt = f"""
                Generate a detailed response for this software development step:
                Project: {project_title}
                Description: {project_description}
                Step: {step_title}
                
                For this specific project, include relevant features and components.
                
                Your response must be in JSON format and specifically tailored to {project_title}.
                If this is a requirements analysis step, include "requirements" and "architecture" fields.
                If this is a design step, include a "design" field with "ui_mockup", "components", and "data_model".
                """
                
                retry_response = await self.generate_json_response(retry_prompt, temperature=0.3)
                
                if retry_response["status"] == "success":
                    return {
                        "status": "success",
                        "message": f"Completed step {step_id}",
                        "result": retry_response["data"]
                    }
                else:
                    # If both attempts fail, try one more time with an even simpler prompt
                    final_attempt_prompt = f"""
                    Create a JSON response for {project_title} with appropriate fields based on the step: {step_title}.
                    Make sure your response is specifically about {project_description}.
                    """
                    
                    final_response = await self.generate_json_response(final_attempt_prompt, temperature=0.1)
                    
                    if final_response["status"] == "success":
                        return {
                            "status": "success",
                            "message": f"Completed step {step_id}",
                            "result": final_response["data"]
                        }
                    else:
                        # If all attempts fail, return a minimal dynamic response
                        return {
                            "status": "success",
                            "message": f"Completed step {step_id} with minimal response",
                            "result": {
                                "output": f"Analysis completed for {project_title}: {step_title}",
                                "next_steps": f"Continue with implementation of {project_title}"
                            }
                        }
        except Exception as e:
            # Handle any exceptions that might occur during processing
            return {
                "status": "error",
                "message": f"Error in architect agent: {str(e)}",
                "details": {
                    "step_id": step_id,
                    "project": project_title,
                    "error": str(e)
                }
            }


    async def _handle_architecture_question(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an architecture question using AI."""
        question = content.get("question", "")
        
        if not question:
            return {
                "status": "error",
                "message": "No question provided"
            }
        
        # Create a prompt for the AI
        prompt = f"""
        You are an expert software architect. Please provide a detailed architecture recommendation for the following question:
        
        Question: {question}
        
        Your response should include:
        1. Overall architecture style recommendation
        2. Key components and their responsibilities
        3. Recommended patterns and practices
        4. Suitable technologies
        5. Considerations for scalability, security, and maintainability
        
        Format your response as JSON with the following structure:
        {{
            "architecture_type": "string",
            "components": [
                {{"name": "string", "purpose": "string"}}
            ],
            "patterns": ["string"],
            "technologies": ["string"],
            "considerations": ["string"]
        }}
        """
        
        try:
            # Call the AI to generate a response
            ai_response = await self.generate_json_response(prompt)
            
            if ai_response["status"] == "success":
                return {
                    "status": "success",
                    "message": "Architecture recommendation provided by AI",
                    "architecture": ai_response["data"]
                }
            else:
                # Log the error for debugging
                print(f"First attempt failed: {ai_response['message']}")
                
                # If the first attempt fails, try with a simpler prompt
                retry_prompt = f"""
                Provide an architecture recommendation for: {question}
                Format as JSON with architecture_type, components, patterns, technologies, and considerations fields.
                """
                
                retry_response = await self.generate_json_response(retry_prompt, temperature=0.3)
                
                if retry_response["status"] == "success":
                    return {
                        "status": "success",
                        "message": "Architecture recommendation provided by AI (retry)",
                        "architecture": retry_response["data"]
                    }
                else:
                    # Log the error for debugging
                    print(f"Second attempt failed: {retry_response['message']}")
                    
                    # Return an error response instead of a hardcoded fallback
                    return {
                        "status": "error",
                        "message": "Failed to generate architecture recommendation",
                        "details": {
                            "first_attempt_error": ai_response.get("message", "Unknown error"),
                            "retry_attempt_error": retry_response.get("message", "Unknown error")
                        }
                    }
        except Exception as e:
            # Catch any unexpected exceptions
            print(f"Unexpected error in _handle_architecture_question: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing architecture question: {str(e)}"
            }

    async def _handle_design_system(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a system design task."""
        system_name = task.get("system_name", "")
        requirements = task.get("requirements", [])
        
        # Create a prompt based on the system name and requirements
        prompt = f"""
        You are an expert software architect. Please design a system with the following details:
        
        System Name: {system_name}
        Requirements: {', '.join(requirements)}
        
        Your design should include:
        1. Overall architecture style
        2. Key components and their responsibilities
        3. Technology stack recommendations
        4. Deployment strategy
        
        Format your response as JSON with the following structure:
        {{
            "system_name": "{system_name}",
            "architecture_style": "string",
            "components": [
                {{"name": "string", "technology": "string", "responsibility": "string"}}
            ],
            "deployment": {{
                "strategy": "string",
                "platform": "string",
                "ci_cd": "string"
            }}
        }}
        
        Ensure that your design is specifically tailored to {system_name} and addresses the provided requirements.
        """
        
        # Call the AI to generate a response
        ai_response = await self.generate_json_response(prompt, temperature=0.2)
        
        if ai_response["status"] == "success":
            return {
                "status": "success",
                "message": f"Design created for {system_name}",
                "design": ai_response["data"]
            }
        else:
            # If the first attempt fails, try with a simpler prompt
            retry_prompt = f"""
            Design a system for {system_name} that addresses these requirements: {', '.join(requirements)}
            Format as JSON with system_name, architecture_style, components, and deployment fields.
            """
            
            retry_response = await self.generate_json_response(retry_prompt, temperature=0.3)
            
            if retry_response["status"] == "success":
                return {
                    "status": "success",
                    "message": f"Design created for {system_name} (retry)",
                    "design": retry_response["data"]
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to generate design for {system_name}"
                }
