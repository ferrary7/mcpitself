import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

class MemoryStorage:
    """Simple JSON-based storage for MCP memory."""
    
    def __init__(self, storage_dir: str = "memory_data"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize storage files
        self.tasks_file = os.path.join(storage_dir, "tasks.json")
        self.messages_file = os.path.join(storage_dir, "messages.json")
        self.agents_file = os.path.join(storage_dir, "agents.json")
        self.context_file = os.path.join(storage_dir, "context.json")
        
        # Create files if they don't exist
        for file_path in [self.tasks_file, self.messages_file, self.agents_file, self.context_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    def _read_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Read JSON data from a file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_json(self, file_path: str, data: List[Dict[str, Any]]) -> None:
        """Write JSON data to a file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    # Task operations
    def save_task(self, task: Dict[str, Any]) -> str:
        """Save a task to storage and return its ID."""
        tasks = self._read_json(self.tasks_file)
        
        # Generate ID if not present
        if 'task_id' not in task:
            task['task_id'] = str(uuid.uuid4())
        
        # Add timestamps
        task['created_at'] = task.get('created_at', datetime.now().isoformat())
        task['updated_at'] = datetime.now().isoformat()
        
        # Check if task already exists
        for i, existing_task in enumerate(tasks):
            if existing_task.get('task_id') == task['task_id']:
                tasks[i] = task
                self._write_json(self.tasks_file, tasks)
                return task['task_id']
        
        # Add new task
        tasks.append(task)
        self._write_json(self.tasks_file, tasks)
        return task['task_id']
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID."""
        tasks = self._read_json(self.tasks_file)
        for task in tasks:
            if task.get('task_id') == task_id:
                return task
        return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks."""
        return self._read_json(self.tasks_file)
    
    # Message operations
    def save_message(self, message: Dict[str, Any]) -> str:
        """Save a message to storage and return its ID."""
        messages = self._read_json(self.messages_file)
        
        # Generate ID if not present
        if 'message_id' not in message:
            message['message_id'] = str(uuid.uuid4())
        
        # Add timestamp if not present
        message['timestamp'] = message.get('timestamp', datetime.now().isoformat())
        
        messages.append(message)
        self._write_json(self.messages_file, messages)
        return message['message_id']
    
    def get_messages(self, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get messages with optional filtering."""
        messages = self._read_json(self.messages_file)
        
        if not filter_dict:
            return messages
        
        filtered_messages = []
        for message in messages:
            match = True
            for key, value in filter_dict.items():
                if key not in message or message[key] != value:
                    match = False
                    break
            if match:
                filtered_messages.append(message)
        
        return filtered_messages
    
    # Agent operations
    def register_agent(self, agent_info: Dict[str, Any]) -> str:
        """Register an agent in the system."""
        agents = self._read_json(self.agents_file)
        
        # Generate ID if not present
        if 'agent_id' not in agent_info:
            agent_info['agent_id'] = str(uuid.uuid4())
        
        # Check if agent already exists
        for i, existing_agent in enumerate(agents):
            if existing_agent.get('agent_id') == agent_info['agent_id']:
                agents[i] = agent_info
                self._write_json(self.agents_file, agents)
                return agent_info['agent_id']
        
        # Add new agent
        agents.append(agent_info)
        self._write_json(self.agents_file, agents)
        return agent_info['agent_id']
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information by ID."""
        agents = self._read_json(self.agents_file)
        for agent in agents:
            if agent.get('agent_id') == agent_id:
                return agent
        return None
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all registered agents."""
        return self._read_json(self.agents_file)
    
    # Context operations
    def save_context(self, key: str, value: Any) -> None:
        """Save a context value with the given key."""
        context = self._read_json(self.context_file)
        
        # Convert to dict if it's a list
        if isinstance(context, list):
            context_dict = {}
            for item in context:
                if isinstance(item, dict) and 'key' in item and 'value' in item:
                    context_dict[item['key']] = item['value']
            context = context_dict
        
        context[key] = value
        
        # Convert back to list format for storage
        context_list = [{'key': k, 'value': v} for k, v in context.items()]
        self._write_json(self.context_file, context_list)
    
    def get_context(self, key: str = None) -> Any:
        """Get a context value by key, or all context if no key provided."""
        context_list = self._read_json(self.context_file)
        
        # Convert to dict
        context = {}
        for item in context_list:
            if isinstance(item, dict) and 'key' in item and 'value' in item:
                context[item['key']] = item['value']
        
        if key:
            return context.get(key)
        return context