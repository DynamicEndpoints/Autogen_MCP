# Enhanced AutoGen MCP Server

[![smithery badge](https://smithery.ai/badge/@DynamicEndpoints/autogen_mcp)](https://smithery.ai/server/@DynamicEndpoints/autogen_mcp)

A comprehensive MCP server that provides deep integration with Microsoft's AutoGen framework v0.9+, featuring the latest capabilities including prompts, resources, advanced workflows, and enhanced agent types. This server enables sophisticated multi-agent conversations through a standardized Model Context Protocol interface.

## 🚀 Latest Features (v0.2.0)

### ✨ **Enhanced MCP Support**
- **Prompts**: Pre-built templates for common workflows (code review, research, creative writing)
- **Resources**: Real-time access to agent status, chat history, and configurations
- **Dynamic Content**: Template-based prompts with arguments and embedded resources
- **Latest MCP SDK**: Version 1.12.3 with full feature support

### 🤖 **Advanced Agent Types**
- **Assistant Agents**: Enhanced with latest LLM capabilities
- **Conversable Agents**: Flexible conversation patterns
- **Teachable Agents**: Learning and memory persistence
- **Retrievable Agents**: Knowledge base integration
- **Multimodal Agents**: Image and document processing (when available)

### 🔄 **Sophisticated Workflows**
- **Code Generation**: Architect → Developer → Reviewer → Executor pipeline
- **Research Analysis**: Researcher → Analyst → Critic → Synthesizer workflow
- **Creative Writing**: Multi-stage creative collaboration
- **Problem Solving**: Structured approach to complex problems
- **Code Review**: Security → Performance → Style review teams
- **Custom Workflows**: Build your own agent collaboration patterns

### 🎯 **Enhanced Chat Capabilities**
- **Smart Speaker Selection**: Auto, manual, random, round-robin modes
- **Nested Conversations**: Hierarchical agent interactions
- **Swarm Intelligence**: Coordinated multi-agent problem solving
- **Memory Management**: Persistent agent knowledge and preferences
- **Quality Checks**: Built-in validation and improvement loops

## 🛠️ Available Tools

### Core Agent Management
- `create_agent` - Create agents with advanced configurations
- `create_workflow` - Build complete multi-agent workflows
- `get_agent_status` - Detailed agent metrics and health monitoring

### Conversation Execution
- `execute_chat` - Enhanced two-agent conversations
- `execute_group_chat` - Multi-agent group discussions
- `execute_nested_chat` - Hierarchical conversation structures
- `execute_swarm` - Swarm-based collaborative problem solving

### Workflow Orchestration
- `execute_workflow` - Run predefined workflow templates
- `manage_agent_memory` - Handle agent learning and persistence
- `configure_teachability` - Enable/configure agent learning capabilities

## 📝 Available Prompts

### `autogen-workflow`
Create sophisticated multi-agent workflows with customizable parameters:
- **Arguments**: `task_description`, `agent_count`, `workflow_type`
- **Use case**: Rapid workflow prototyping and deployment

### `code-review`
Set up collaborative code review with specialized agents:
- **Arguments**: `code`, `language`, `focus_areas`
- **Use case**: Comprehensive code quality assessment

### `research-analysis`
Deploy research teams for in-depth topic analysis:
- **Arguments**: `topic`, `depth`
- **Use case**: Academic research, market analysis, technical investigation

## 📊 Available Resources

### `autogen://agents/list`
Live list of active agents with status and capabilities

### `autogen://workflows/templates`
Available workflow templates and configurations

### `autogen://chat/history`
Recent conversation history and interaction logs

### `autogen://config/current`
Current server configuration and settings

## Installation

### Installing via Smithery

To install AutoGen Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@DynamicEndpoints/autogen_mcp):

```bash
npx -y @smithery/cli install @DynamicEndpoints/autogen_mcp --client claude
```

### Manual Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/autogen-mcp.git
cd autogen-mcp
```

2. **Install Node.js dependencies:**
```bash
npm install
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt --user
```

4. **Build the TypeScript project:**
```bash
npm run build
```

5. **Set up configuration:**
```bash
cp .env.example .env
cp config.json.example config.json
# Edit .env and config.json with your settings
```

## Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key-here

# Optional - Path to configuration file
AUTOGEN_MCP_CONFIG=config.json

# Enhanced Features
ENABLE_PROMPTS=true
ENABLE_RESOURCES=true
ENABLE_WORKFLOWS=true
ENABLE_TEACHABILITY=true

# Performance Settings
MAX_CHAT_TURNS=10
DEFAULT_OUTPUT_FORMAT=json
```

### Configuration File

Update `config.json` with your preferences:

```json
{
  "llm_config": {
    "config_list": [
      {
        "model": "gpt-4o",
        "api_key": "your-openai-api-key"
      }
    ],
    "temperature": 0.7
  },
  "enhanced_features": {
    "prompts": { "enabled": true },
    "resources": { "enabled": true },
    "workflows": { "enabled": true }
  }
}
```

## Usage Examples

### Using with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "autogen": {
      "command": "node",
      "args": ["path/to/autogen-mcp/build/index.js"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

### Command Line Testing

Test the server functionality:

```bash
# Run comprehensive tests
python test_server.py

# Test CLI interface
python cli_example.py create_agent "researcher" "assistant" "You are a research specialist"
python cli_example.py execute_workflow "code_generation" '{"task":"Hello world","language":"python"}'
```

### Using Prompts

The server provides several built-in prompts:

1. **autogen-workflow** - Create multi-agent workflows
2. **code-review** - Set up collaborative code review
3. **research-analysis** - Deploy research teams

### Accessing Resources

Available resources provide real-time data:

- `autogen://agents/list` - Current active agents
- `autogen://workflows/templates` - Available workflow templates  
- `autogen://chat/history` - Recent conversation history
- `autogen://config/current` - Server configuration

## Workflow Examples

### Code Generation Workflow

```json
{
  "workflow_name": "code_generation",
  "input_data": {
    "task": "Create a REST API endpoint",
    "language": "python",
    "requirements": ["FastAPI", "Pydantic", "Error handling"]
  },
  "quality_checks": true
}
```

### Research Workflow

```json
{
  "workflow_name": "research", 
  "input_data": {
    "topic": "AI Ethics in 2025",
    "depth": "comprehensive"
  },
  "output_format": "markdown"
}
```

## Advanced Features

### Agent Types

- **Assistant Agents**: LLM-powered conversational agents
- **User Proxy Agents**: Code execution and human interaction
- **Conversable Agents**: Flexible conversation patterns
- **Teachable Agents**: Learning and memory persistence (when available)
- **Retrievable Agents**: Knowledge base integration (when available)

### Chat Modes

- **Two-Agent Chat**: Direct conversation between agents
- **Group Chat**: Multi-agent discussions with smart speaker selection
- **Nested Chat**: Hierarchical conversation structures  
- **Swarm Intelligence**: Coordinated problem solving (experimental)

### Memory Management

- Persistent agent memory across sessions
- Conversation history tracking
- Learning from interactions (teachable agents)
- Memory cleanup and optimization

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your OpenAI API key is valid and has sufficient credits
2. **Import Errors**: Install all dependencies with `pip install -r requirements.txt --user`
3. **Build Failures**: Check Node.js version (>= 18) and run `npm install`
4. **Chat Failures**: Verify agent creation succeeded before attempting conversations

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
python test_server.py
```

### Performance Tips

- Use `gpt-4o-mini` for faster, cost-effective operations
- Enable caching for repeated operations
- Set appropriate timeout values for long-running workflows
- Use quality checks only when needed (increases execution time)

## Development

### Running Tests

```bash
# Full test suite
python test_server.py

# Individual workflow tests  
python -c "
import asyncio
from src.autogen_mcp.workflows import WorkflowManager
wm = WorkflowManager()
print(asyncio.run(wm.execute_workflow('code_generation', {'task': 'test'})))
"
```

### Building

```bash
npm run build
npm run lint
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Version History

### v0.2.0 (Latest)
- ✨ Enhanced MCP support with prompts and resources
- 🤖 Advanced agent types (teachable, retrievable)
- 🔄 Sophisticated workflows with quality checks
- 🎯 Smart speaker selection and nested conversations
- 📊 Real-time resource monitoring
- 🧠 Memory management and persistence

### v0.1.0
- Basic AutoGen integration
- Simple agent creation and chat execution
- MCP tool interface

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the test examples in `test_server.py`
- Open an issue on GitHub with detailed reproduction steps

## License

MIT License - see LICENSE file for details.

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
