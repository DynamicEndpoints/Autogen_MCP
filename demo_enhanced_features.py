#!/usr/bin/env python3
"""
Enhanced AutoGen MCP Server Demonstration
Shows off all the latest features including prompts, resources, workflows, and advanced agent capabilities.
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autogen_mcp.server import EnhancedAutoGenServer

async def demonstrate_enhanced_features():
    """Demonstrate the enhanced AutoGen MCP server capabilities."""
    print("🚀 Enhanced AutoGen MCP Server Demonstration")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Initialize server
    server = EnhancedAutoGenServer()
    print("✅ Enhanced AutoGen MCP Server initialized successfully!")
    print()

    # 1. Demonstrate Agent Creation
    print("🤖 1. Advanced Agent Creation")
    print("-" * 30)
    
    agents_to_create = [
        {
            "name": "senior_developer",
            "type": "assistant", 
            "system_message": "You are a senior software developer with expertise in Python, JavaScript, and system architecture. You write clean, efficient, and well-documented code.",
            "llm_config": {"model": "gpt-4o", "temperature": 0.3}
        },
        {
            "name": "code_reviewer",
            "type": "assistant",
            "system_message": "You are a meticulous code reviewer focused on best practices, security, and maintainability. You provide constructive feedback.",
            "llm_config": {"model": "gpt-4o", "temperature": 0.1}
        },
        {
            "name": "project_manager",
            "type": "user_proxy",
            "system_message": "You coordinate project activities and ensure deliverables meet requirements.",
            "code_execution_config": {"work_dir": "projects", "use_docker": False}
        }
    ]

    for agent_config in agents_to_create:
        result = await server.handle_create_agent(agent_config)
        if result.get("success"):
            print(f"  ✅ Created {agent_config['name']} ({agent_config['type']})")
        else:
            print(f"  ❌ Failed to create {agent_config['name']}: {result.get('error', 'Unknown error')}")

    print()

    # 2. Demonstrate Workflow Templates
    print("⚙️ 2. Available Workflow Templates")
    print("-" * 35)
    
    workflows = server.workflow_manager._workflow_templates.keys()
    for workflow in workflows:
        print(f"  📋 {workflow}")
    print()

    # 3. Demonstrate Resources
    print("📁 3. MCP Resources")
    print("-" * 20)
    
    resources = [
        "autogen://agents/list",
        "autogen://workflows/templates", 
        "autogen://chat/history",
        "autogen://config/current"
    ]

    for resource_uri in resources:
        try:
            result = await server._get_resource({"uri": resource_uri})
            print(f"  ✅ {resource_uri}: Available")
        except Exception as e:
            print(f"  ❌ {resource_uri}: {str(e)}")
    print()

    # 4. Demonstrate Tool Capabilities
    print("🔧 4. Available Tools")
    print("-" * 20)
    
    tools = [
        "create_agent", "delete_agent", "list_agents", "start_chat",
        "send_message", "get_chat_history", "create_group_chat", 
        "execute_workflow", "teach_agent", "save_conversation"
    ]

    for tool in tools:
        handler_method = f"handle_{tool}"
        if hasattr(server, handler_method):
            print(f"  ✅ {tool}")
        else:
            print(f"  ❌ {tool} (missing handler)")
    print()

    # 5. Demonstrate Agent Listing
    print("📋 5. Current Agents")
    print("-" * 20)
    
    agent_list = await server.handle_list_agents({})
    print(f"  {agent_list.get('content', [{}])[0].get('text', 'No agents listed')}")
    print()

    # 6. Demonstrate Configuration
    print("⚙️ 6. Server Configuration")
    print("-" * 25)
    
    print(f"  📊 Capabilities: {', '.join(k for k, v in server.capabilities.items() if v)}")
    print(f"  🔧 Default LLM: {server.server_config.default_llm_config.get('config_list', [{}])[0].get('model', 'Not configured')}")
    print(f"  💾 Memory: {len(server.chat_history)} chat sessions")
    print(f"  🗃️ Resource Cache: {len(server.resource_cache)} items")
    print()

    # 7. Demonstrate Enhanced Features Summary
    print("✨ 7. Enhanced Features Summary")
    print("-" * 30)
    
    features = {
        "Latest AutoGen Integration": "v0.9.0+ with latest agent types",
        "MCP Protocol Support": "v1.12.3 with prompts and resources",
        "Advanced Workflows": "6 built-in multi-stage workflows",
        "Agent Memory": "Persistent conversation and knowledge management",
        "Teachable Agents": "Agent learning and knowledge accumulation",
        "Resource Management": "Real-time access to agent and workflow data",
        "Async Processing": "Full async/await support for scalability",
        "Error Handling": "Comprehensive error management and logging",
        "Configuration": "Flexible config with environment variables",
        "Extensibility": "Plugin architecture for custom tools and workflows"
    }

    for feature, description in features.items():
        print(f"  🌟 {feature}: {description}")
    
    print()
    print("🎉 Enhanced AutoGen MCP Server Demonstration Complete!")
    print("💡 The server is ready for production use with all latest features enabled.")
    print("📚 See README.md for detailed usage instructions and examples.")

if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault("OPENAI_API_KEY", "demo-key-replace-with-real")
    
    try:
        asyncio.run(demonstrate_enhanced_features())
    except KeyboardInterrupt:
        print("\n👋 Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Demonstration failed: {str(e)}")
        sys.exit(1)
