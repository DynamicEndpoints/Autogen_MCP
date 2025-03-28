# AutoGen MCP Server

An MCP server that provides integration with Microsoft's AutoGen framework, enabling multi-agent conversations through a standardized interface. This server allows you to create and manage AI agents that can collaborate and solve problems through natural language interactions.

## Features

- Create and manage AutoGen agents with customizable configurations
- Execute one-on-one conversations between agents
- Orchestrate group chats with multiple agents
- Configurable LLM settings and code execution environments
- Support for both assistant and user proxy agents
- Built-in error handling and response validation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/autogen-mcp.git
cd autogen-mcp
```

2. Install dependencies:
```bash
pip install -e .
```

## Configuration

### Environment Variables

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Configure the environment variables:
```bash
# Path to the configuration file
AUTOGEN_MCP_CONFIG=config.json

# OpenAI API Key (optional, can also be set in config.json)
OPENAI_API_KEY=your-openai-api-key
```

### Server Configuration

1. Copy `config.json.example` to `config.json`:
```bash
cp config.json.example config.json
```

2. Configure the server settings:
```json
{
  "llm_config": {
    "config_list": [
      {
        "model": "gpt-4",
        "api_key": "your-openai-api-key"
      }
    ],
    "temperature": 0
  },
  "code_execution_config": {
    "work_dir": "workspace",
    "use_docker": false
  }
}
```

## Available Operations

The server supports three main operations:

### 1. Creating Agents

```json
{
  "name": "create_agent",
  "arguments": {
    "name": "tech_lead",
    "type": "assistant",
    "system_message": "You are a technical lead with expertise in software architecture and design patterns."
  }
}
```

### 2. One-on-One Chat

```json
{
  "name": "execute_chat",
  "arguments": {
    "initiator": "agent1",
    "responder": "agent2",
    "message": "Let's discuss the system architecture."
  }
}
```

### 3. Group Chat

```json
{
  "name": "execute_group_chat",
  "arguments": {
    "agents": ["agent1", "agent2", "agent3"],
    "message": "Let's review the proposed solution."
  }
}
```

## Error Handling

Common error scenarios include:

1. Agent Creation Errors
```json
{
  "error": "Agent already exists"
}
```

2. Execution Errors
```json
{
  "error": "Agent not found"
}
```

3. Configuration Errors
```json
{
  "error": "AUTOGEN_MCP_CONFIG environment variable not set"
}
```

## Architecture

The server follows a modular architecture:

```
src/
├── autogen_mcp/
│   ├── __init__.py
│   ├── agents.py      # Agent management and configuration
│   ├── config.py      # Configuration handling and validation
│   ├── server.py      # MCP server implementation
│   └── workflows.py   # Conversation workflow management
```

## License

MIT License - See LICENSE file for details
