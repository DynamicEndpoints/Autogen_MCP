#!/usr/bin/env python3
"""
CLI Example for Enhanced AutoGen MCP Server
Demonstrates how to use the server in command-line mode.
"""

import json
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def show_help():
    """Show available commands and usage."""
    print("""
Enhanced AutoGen MCP Server - CLI Interface

Usage: python cli_example.py <command> [arguments]

Available Commands:

Agent Management:
  create_agent <name> <type> [system_message]
    - Create a new agent
    - Types: assistant, user_proxy, conversable, teachable, retrievable
    
  agent_status [agent_name]
    - Get status of specific agent or all agents

Chat Execution:
  chat <initiator> <responder> <message>
    - Execute a simple chat between two agents
    
  group_chat <agent1,agent2,agent3> <initiator> <message>
    - Execute a group chat with multiple agents

Workflow Management:
  create_workflow <name> <type> <task>
    - Create a new workflow
    - Types: sequential, group_chat, nested, swarm, hierarchical
    
  execute_workflow <workflow_name> <input_data>
    - Execute a predefined workflow

Resources:
  list_agents       - List all active agents
  list_workflows    - List available workflow templates
  chat_history      - Show recent chat history
  config            - Show current configuration

Examples:
  python cli_example.py create_agent "researcher" "assistant" "You are a research specialist"
  python cli_example.py chat "researcher" "analyst" "Please research AI trends"
  python cli_example.py execute_workflow "code_generation" '{"task":"Hello world program","language":"python"}'
  python cli_example.py list_agents
""")

def execute_command(command, args):
    """Execute a command with the AutoGen MCP server."""
    # This would normally connect to the MCP server
    # For demo purposes, we'll show the structure
    
    if command == "create_agent":
        if len(args) < 2:
            print("Error: create_agent requires name and type")
            return
        
        agent_data = {
            "name": args[0],
            "type": args[1],
            "system_message": args[2] if len(args) > 2 else f"You are a helpful {args[1]} agent."
        }
        
        print(f"Creating agent: {json.dumps(agent_data, indent=2)}")
        print("Command would be sent to MCP server: create_agent")
        
    elif command == "chat":
        if len(args) < 3:
            print("Error: chat requires initiator, responder, and message")
            return
            
        chat_data = {
            "initiator": args[0],
            "responder": args[1], 
            "message": " ".join(args[2:])
        }
        
        print(f"Executing chat: {json.dumps(chat_data, indent=2)}")
        print("Command would be sent to MCP server: execute_chat")
        
    elif command == "group_chat":
        if len(args) < 3:
            print("Error: group_chat requires agent_list, initiator, and message")
            return
            
        chat_data = {
            "agent_names": args[0].split(","),
            "initiator": args[1],
            "message": " ".join(args[2:])
        }
        
        print(f"Executing group chat: {json.dumps(chat_data, indent=2)}")
        print("Command would be sent to MCP server: execute_group_chat")
        
    elif command == "execute_workflow":
        if len(args) < 2:
            print("Error: execute_workflow requires workflow_name and input_data")
            return
            
        try:
            input_data = json.loads(args[1])
        except json.JSONDecodeError:
            print("Error: input_data must be valid JSON")
            return
            
        workflow_data = {
            "workflow_name": args[0],
            "input_data": input_data
        }
        
        print(f"Executing workflow: {json.dumps(workflow_data, indent=2)}")
        print("Command would be sent to MCP server: execute_workflow")
        
    elif command == "list_agents":
        print("Getting resource: autogen://agents/list")
        print("Command would be sent to MCP server: get_resource")
        
    elif command == "list_workflows":
        print("Getting resource: autogen://workflows/templates")
        print("Command would be sent to MCP server: get_resource")
        
    elif command == "chat_history":
        print("Getting resource: autogen://chat/history")
        print("Command would be sent to MCP server: get_resource")
        
    elif command == "config":
        print("Getting resource: autogen://config/current")
        print("Command would be sent to MCP server: get_resource")
        
    elif command == "agent_status":
        status_data = {
            "include_metrics": True,
            "include_memory": True
        }
        if args:
            status_data["agent_name"] = args[0]
            
        print(f"Getting agent status: {json.dumps(status_data, indent=2)}")
        print("Command would be sent to MCP server: get_agent_status")
        
    else:
        print(f"Unknown command: {command}")
        show_help()

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        show_help()
        return
        
    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    print(f"Enhanced AutoGen MCP Server - CLI Mode")
    print(f"Command: {command}")
    print(f"Arguments: {args}")
    print("-" * 40)
    
    execute_command(command, args)
    
    print("\n" + "-" * 40)
    print("Note: This is a demonstration CLI. In production, these commands")
    print("would be sent to the actual MCP server running in stdio mode.")

if __name__ == "__main__":
    main()
