# Add this function to clear agent cache
async def clear_agent_cache():
    """Clear any cached context in agents to prevent contamination between projects."""
    # Reset the agents.json file to only contain the base agents
    base_agents = [
        {
            "agent_id": "7514baf0-599b-47ef-b6b2-c5f48031b461",
            "name": "PlannerAgent",
            "type": "PlannerAgent"
        },
        {
            "agent_id": "ee25eaf7-58ae-4411-aa59-4367fee3d7da",
            "name": "CoderAgent",
            "type": "CoderAgent"
        },
        {
            "agent_id": "6c720d68-dfa0-4bcc-a897-4f83cb175454",
            "name": "MemoryAgent",
            "type": "MemoryAgent"
        },
        {
            "agent_id": "1cf32b15-2849-4d5e-ae10-c2aab6bbb59c",
            "name": "ArchitectAgent",
            "type": "ArchitectAgent"
        }
    ]
    
    with open("memory_data/agents.json", "w") as f:
        json.dump(base_agents, f, indent=2)
    
    # You may also want to clear any other cached data
    # For example, if you have a memory store or context cache

# Call this function when creating a new goal
@app.post("/goals")
async def create_goal(goal: GoalCreate):
    await clear_agent_cache()  # Clear cache before creating a new goal
    # Rest of your existing code...