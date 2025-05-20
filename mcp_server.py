import os
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from pydantic import BaseModel

# Import our components
from agents.planner_agent import PlannerAgent
from agents.coder_agent import CoderAgent
from agents.memory_agent import MemoryAgent
from agents.architect_agent import ArchitectAgent
from memory.storage import MemoryStorage
from schemas.message import Message, Task, MessageType, MessagePriority

# Create the FastAPI app
app = FastAPI(
    title="MCP Server",
    description="A minimal MCP server that can talk to agents, store memory, and serve user tasks",
    version="0.1.0"
)

# Initialize storage
storage = MemoryStorage(storage_dir="memory_data")

# Initialize agents
planner_agent = PlannerAgent(name="PlannerAgent")
coder_agent = CoderAgent(name="CoderAgent")
memory_agent = MemoryAgent(name="MemoryAgent", storage=storage)
architect_agent = ArchitectAgent(name="ArchitectAgent")

# Register agents in storage
agents = {
    "planner": planner_agent,
    "coder": coder_agent,
    "memory": memory_agent,
    "architect": architect_agent
}

for agent_id, agent in agents.items():
    storage.register_agent(agent.get_agent_info())

# Task queue for background processing
task_queue = []

# Helper functions
async def process_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Process a message by routing it to the appropriate agent."""
    recipient = message.get("recipient", "")
    
    if recipient not in agents:
        return {
            "status": "error",
            "message": f"Unknown recipient: {recipient}",
            "timestamp": datetime.now().isoformat()
        }
    
    # Store the message
    storage.save_message(message)
    
    # Process the message with the appropriate agent
    response = await agents[recipient].process_message(message)
    
    # Create a response message
    response_message = {
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "sender": recipient,
        "recipient": message.get("sender", "user"),
        "message_type": "response",
        "priority": message.get("priority", "medium"),
        "content": response,
        "parent_id": message.get("message_id")
    }
    
    # Store the response
    storage.save_message(response_message)
    
    return response_message

async def process_task_in_background(task: Dict[str, Any]) -> None:
    """Process a task in the background."""
    # First, plan the task
    plan_message = {
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "sender": "mcp",
        "recipient": "planner",
        "message_type": "task",
        "priority": "medium",
        "content": {
            "type": "plan_goal",
            "goal": task.get("title", "") + ": " + task.get("description", "")
        }
    }
    
    plan_response = await process_message(plan_message)
    plan = plan_response.get("content", {}).get("plan", {})
    
    # Create a copy of the task to avoid circular references
    task_update = task.copy()
    task_update["plan"] = plan
    task_update["status"] = "planned"
    storage.save_task(task_update)
    
    # Process each step in the plan
    steps = plan.get("steps", [])
    for step in steps:
        # Check dependencies
        dependencies = step.get("depends_on", [])
        all_dependencies_met = True
        
        for dep_id in dependencies:
            # Find the dependency step
            dep_step = next((s for s in steps if s.get("id") == dep_id), None)
            if not dep_step or dep_step.get("status") != "completed":
                all_dependencies_met = False
                break
        
        if not all_dependencies_met:
            continue
        
        # Assign the step to the appropriate agent
        assigned_to = step.get("assigned_to", "").split("_")[0]  # Extract agent type from "agent_name"
        if assigned_to not in agents:
            # Default to architect if unknown
            assigned_to = "architect"
        
        step_message = {
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "sender": "mcp",
            "recipient": assigned_to,
            "message_type": "task",
            "priority": "medium",
            "content": {
                "type": "execute_step",
                "step": step,
                "task_id": task.get("task_id"),
                # Create a simplified context to avoid circular references
                "context": {
                    "task_id": task.get("task_id"),
                    "title": task.get("title"),
                    "description": task.get("description")
                }
            }
        }
        
        step_response = await process_message(step_message)
        
        # Update the step status
        step["status"] = "completed" if step_response.get("content", {}).get("status") == "success" else "failed"
        step["result"] = step_response.get("content", {})
        
        # Create a new copy of the task for each update
        task_update = storage.get_task(task.get("task_id"))
        if task_update:
            # Update the step in the plan
            for i, s in enumerate(task_update.get("plan", {}).get("steps", [])):
                if s.get("id") == step.get("id"):
                    task_update["plan"]["steps"][i] = step
            
            task_update["updated_at"] = datetime.now().isoformat()
            storage.save_task(task_update)
    
    # Check if all steps are completed
    all_completed = all(step.get("status") == "completed" for step in steps)
    
    # Final update to the task
    task_update = storage.get_task(task.get("task_id"))
    if task_update:
        task_update["status"] = "completed" if all_completed else "partially_completed"
        task_update["updated_at"] = datetime.now().isoformat()
        storage.save_task(task_update)

# API routes
@app.get("/")
async def root():
    """Root endpoint that returns basic server information."""
    return {
        "name": "MCP Server",
        "version": "0.1.0",
        "status": "running",
        "agents": list(agents.keys()),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/goals")
async def create_goal(
    background_tasks: BackgroundTasks,
    goal: Dict[str, Any] = Body(...)
):
    """Create a new goal for the MCP to process."""
    # Validate the goal
    if "title" not in goal or "description" not in goal:
        raise HTTPException(status_code=400, detail="Goal must include title and description")
    
    # Create a task from the goal
    task = {
        "task_id": str(uuid.uuid4()),
        "title": goal.get("title"),
        "description": goal.get("description"),
        "assigned_to": "mcp",
        "created_by": goal.get("created_by", "user"),
        "status": "pending",
        "priority": goal.get("priority", "medium"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Save the task
    task_id = storage.save_task(task)
    
    # Process the task in the background
    background_tasks.add_task(process_task_in_background, task)
    
    return {
        "status": "accepted",
        "message": "Goal accepted for processing",
        "task_id": task_id
    }

@app.get("/goals/{task_id}")
async def get_goal(task_id: str):
    """Get the status and details of a goal."""
    task = storage.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Goal with ID {task_id} not found")
    
    return task

@app.get("/goals")
async def list_goals():
    """List all goals."""
    return storage.get_all_tasks()

@app.post("/messages")
async def send_message(message: Dict[str, Any] = Body(...)):
    """Send a message to an agent."""
    # Validate the message
    required_fields = ["sender", "recipient", "message_type", "content"]
    for field in required_fields:
        if field not in message:
            raise HTTPException(status_code=400, detail=f"Message must include {field}")
    
    # Add message ID and timestamp if not present
    if "message_id" not in message:
        message["message_id"] = str(uuid.uuid4())
    
    if "timestamp" not in message:
        message["timestamp"] = datetime.now().isoformat()
    
    # Process the message
    response = await process_message(message)
    
    return response

@app.get("/messages")
async def list_messages(
    sender: Optional[str] = None,
    recipient: Optional[str] = None,
    message_type: Optional[str] = None
):
    """List messages with optional filtering."""
    filter_dict = {}
    
    if sender:
        filter_dict["sender"] = sender
    
    if recipient:
        filter_dict["recipient"] = recipient
    
    if message_type:
        filter_dict["message_type"] = message_type
    
    return storage.get_messages(filter_dict)

@app.get("/agents")
async def list_agents():
    """List all registered agents."""
    return storage.get_all_agents()

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get information about a specific agent."""
    agent = storage.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    
    return agent

@app.post("/self-improve")
async def self_improve(background_tasks: BackgroundTasks):
    """Trigger the MCP to improve itself."""
    # Create a self-improvement goal
    goal = {
        "title": "Improve MCP System",
        "description": "Analyze the current MCP system and suggest improvements",
        "created_by": "mcp",
        "priority": "high"
    }
    
    # Create a task from the goal
    task = {
        "task_id": str(uuid.uuid4()),
        "title": goal.get("title"),
        "description": goal.get("description"),
        "assigned_to": "mcp",
        "created_by": goal.get("created_by", "mcp"),
        "status": "pending",
        "priority": goal.get("priority", "high"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Save the task
    task_id = storage.save_task(task)
    
    # Process the task in the background
    background_tasks.add_task(process_task_in_background, task)
    
    return {
        "status": "accepted",
        "message": "Self-improvement process initiated",
        "task_id": task_id
    }

if __name__ == "__main__":
    # Run the server
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=8000, reload=True)
