# Model Context Protocol (MCP) Server

The MCP server, named `mcpitself`, is designed to facilitate the creation and management of Model Context Protocols. It leverages a multi-agent system to automate and streamline the development of new MCPs.

## Overview

`mcpitself` is a sophisticated system that uses specialized agents to collaborate on software development tasks. These agents communicate through a structured message-passing system and can handle various tasks like planning projects, designing architectures, and writing code.

## Key Features

- **Collaborative Multi-Agent System**: Includes Planner, Architect, Coder, and Memory agents, each with specialized roles.
- **AI-Powered Decision Making**: Utilizes the Gemini API for generating intelligent responses and content.
- **Persistent Memory**: Stores conversation history and agent states for future reference.
- **Extensible and Modular**: Designed to be easily extended with new agents or capabilities.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mcpitself.git
   cd mcpitself
   ```
2. Install dependencies:
   
   ```bash
   pip install -r requirements.txt
    ```
3. Set up environment variables:
   
   - Copy .env.example to .env and update with your API keys
   - Or set environment variables manually


## Configuration
The application uses environment variables for configuration:

- GEMINI_API_KEY : Your Gemini API key
- GEMINI_API_URL : The Gemini API endpoint
- PORT : Server port (default: 8000)
- HOST : Server host (default: 0.0.0.0)
- DEBUG : Debug mode (True/False)
- MEMORY_STORAGE_PATH : Path to store memory data


## Usage
1. Start the server:
   
   ```bash
   uvicorn app:app --reload
    ```
2. Access the API at http://localhost:8000
3. Send messages to agents using the /messages endpoint:
   
   ```bash
   curl -X 'POST' \
     'http://localhost:8000/messages' \
     -H 'accept: application/json' \
     -H 'Content-Type: application/json' \
     -d '{
       "sender": "user",
       "recipient": "architect",
       "message_type": "query",
       "content": {
         "type": "architecture_question",
         "question": "What architecture would you recommend for a high-traffic e-commerce platform?"
       }
     }'
    ```
   ```
## Agent Types
- PlannerAgent : Breaks down goals into actionable steps
- ArchitectAgent : Provides architecture recommendations and designs
- CoderAgent : Writes and reviews code
- MemoryAgent : Manages system memory and retrieves relevant information


## Project Structure
```plaintext
mcpitself/
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── architect_agent.py
│   ├── base_agent.py
│   ├── coder_agent.py
│   ├── memory_agent.py
│   └── planner_agent.py
├── memory_data/            # Persistent storage
│   ├── agents.json
│   └── messages.json
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── ai_integration.py
├── app.py                  # Main application
├── requirements.txt        # Dependencies
├── .env                    # Environment variables (production)
├── .env.example            # Example environment variables
└── README.md               # This file
 ```
```

## API Endpoints
- POST /messages : Send a message to an agent
- GET /messages : Get all messages
- POST /goals : Create a new goal
- GET /goals : Get all goals
- GET /goals/{task_id} : Get a specific goal
- GET /agents : Get all agents
- GET /agents/{agent_id} : Get a specific agent
- POST /self-improve : Self-improve the system
