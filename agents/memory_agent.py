from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

class MemoryAgent(BaseAgent):
    """Agent responsible for storing and retrieving memory."""
    
    def __init__(self, agent_id: str = None, name: str = "MemoryAgent", storage=None):
        super().__init__(agent_id, name)
        self.storage = storage
    
    def set_storage(self, storage):
        """Set the storage backend for this agent."""
        self.storage = storage
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming message."""
        if message.get("message_type") == "task":
            return await self.handle_task(message.get("content", {}))
        
        return {
            "status": "error",
            "message": "Unsupported message type",
            "original_message": message
        }
    
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a memory-related task."""
        if not self.storage:
            return {
                "status": "error",
                "message": "No storage backend configured for MemoryAgent"
            }
        
        task_type = task.get("type", "")
        
        if task_type == "store":
            return await self._store_memory(task)
        elif task_type == "retrieve":
            return await self._retrieve_memory(task)
        elif task_type == "update":
            return await self._update_memory(task)
        elif task_type == "delete":
            return await self._delete_memory(task)
        elif task_type == "search":
            return await self._search_memory(task)
        
        return {
            "status": "error",
            "message": f"Unsupported task type: {task_type}",
            "task": task
        }
    
    async def _store_memory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Store data in memory."""
        memory_type = task.get("memory_type", "")
        data = task.get("data", {})
        
        if not memory_type or not data:
            return {
                "status": "error",
                "message": "Missing memory_type or data for storage"
            }
        
        try:
            if memory_type == "task":
                memory_id = self.storage.save_task(data)
            elif memory_type == "message":
                memory_id = self.storage.save_message(data)
            elif memory_type == "agent":
                memory_id = self.storage.register_agent(data)
            elif memory_type == "context":
                key = task.get("key", "")
                if not key:
                    return {
                        "status": "error",
                        "message": "Missing key for context storage"
                    }
                self.storage.save_context(key, data)
                memory_id = key
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported memory type: {memory_type}"
                }
            
            return {
                "status": "success",
                "message": f"{memory_type} successfully stored",
                "memory_id": memory_id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error storing {memory_type}: {str(e)}"
            }
    
    async def _retrieve_memory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve data from memory."""
        memory_type = task.get("memory_type", "")
        memory_id = task.get("memory_id", "")
        
        if not memory_type:
            return {
                "status": "error",
                "message": "Missing memory_type for retrieval"
            }
        
        try:
            if memory_type == "task":
                if not memory_id:
                    data = self.storage.get_all_tasks()
                else:
                    data = self.storage.get_task(memory_id)
            elif memory_type == "message":
                filter_dict = task.get("filter", {})
                data = self.storage.get_messages(filter_dict)
            elif memory_type == "agent":
                if not memory_id:
                    data = self.storage.get_all_agents()
                else:
                    data = self.storage.get_agent(memory_id)
            elif memory_type == "context":
                key = task.get("key", None)
                data = self.storage.get_context(key)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported memory type: {memory_type}"
                }
            
            return {
                "status": "success",
                "message": f"{memory_type} successfully retrieved",
                "data": data
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error retrieving {memory_type}: {str(e)}"
            }
    
    async def _update_memory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Update data in memory."""
        # For simplicity, we'll reuse the store method since our storage
        # implementation handles updates for existing IDs
        return await self._store_memory(task)
    
    async def _delete_memory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delete data from memory."""
        # Our simple storage doesn't support deletion yet
        return {
            "status": "error",
            "message": "Memory deletion not implemented"
        }
    
    async def _search_memory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Search for data in memory."""
        memory_type = task.get("memory_type", "")
        query = task.get("query", {})
        
        if not memory_type or not query:
            return {
                "status": "error",
                "message": "Missing memory_type or query for search"
            }
        
        # Our simple storage doesn't support advanced search yet
        # We'll just use the retrieve method with filters
        task["filter"] = query
        return await self._retrieve_memory(task)