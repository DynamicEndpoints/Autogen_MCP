#!/usr/bin/env python3
import os
import json
import sys
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv
import autogen
import anyio
from autogen import Agent, AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolRequestSchema, ErrorCode, ListToolsRequestSchema, McpError

from .agents import AgentManager
from .config import ServerConfig, AgentConfig

load_dotenv()

class AutoGenServer:
    def __init__(self):
        """Initialize the agent manager."""
        self.config_path = os.getenv("AUTOGEN_MCP_CONFIG")
        if not self.config_path:
            raise ValueError("AUTOGEN_MCP_CONFIG environment variable not set")

        with open(self.config_path) as f:
            self.config = json.load(f)

        self.server_config = ServerConfig(
            default_llm_config=self.config.get("llm_config"),
            default_code_execution_config=self.config.get("code_execution_config")
        )
        self.agent_manager = AgentManager()
        self.server = Server(
            info={
                "name": "autogen-mcp",
                "version": "0.1.0"
            },
            config={
                "capabilities": {
                    "tools": True
                }
            }
        )

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request_data.get("method")
        params = request_data.get("params", {})

        if method == "list_tools":
            return {
                "tools": [
                    {
                        "name": "create_agent",
                        "description": "Create a new agent",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the agent"
                                },
                                "system_message": {
                                    "type": "string",
                                    "description": "System message for the agent"
                                },
                                "type": {
                                    "type": "string",
                                    "enum": ["assistant", "user_proxy"],
                                    "description": "Type of agent to create"
                                }
                            },
                            "required": ["name", "system_message", "type"]
                        }
                    },
                    {
                        "name": "execute_chat",
                        "description": "Execute a chat between two agents",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "initiator": {
                                    "type": "string",
                                    "description": "Name of the initiating agent"
                                },
                                "responder": {
                                    "type": "string",
                                    "description": "Name of the responding agent"
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Initial message to start the chat"
                                }
                            },
                            "required": ["initiator", "responder", "message"]
                        }
                    },
                    {
                        "name": "execute_group_chat",
                        "description": "Execute a group chat with multiple agents",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "agents": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of agent names to participate"
                                },
                                "message": {
                                    "type": "string",
                                    "description": "Initial message to start the chat"
                                }
                            },
                            "required": ["agents", "message"]
                        }
                    }
                ]
            }

        elif method == "call_tool":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            if tool_name == "create_agent":
                try:
                    agent_config = AgentConfig(
                        name=tool_args["name"],
                        type=tool_args["type"],
                        system_message=tool_args["system_message"],
                        llm_config=self.server_config.get_default_llm_config(),
                        code_execution_config=self.server_config.get_default_code_execution_config() if tool_args["type"] == "assistant" else None
                    )
                    agent = self.agent_manager.create_agent(agent_config)
                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "name": agent.name,
                                "type": tool_args["type"],
                                "system_message": tool_args["system_message"]
                            })
                        }]
                    }
                except Exception as e:
                    return {"error": str(e)}

            elif tool_name == "execute_chat":
                try:
                    initiator = self.agent_manager.get_agent(tool_args["initiator"])
                    responder = self.agent_manager.get_agent(tool_args["responder"])

                    if not initiator or not responder:
                        return {"error": "One or both agents not found"}

                    initiator.initiate_chat(
                        responder,
                        message=tool_args["message"],
                        silent=True,
                        cache_seed=None
                    )

                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "initiator": tool_args["initiator"],
                                "responder": tool_args["responder"],
                                "messages": initiator.chat_messages[responder]
                            })
                        }]
                    }
                except Exception as e:
                    return {"error": str(e)}

            elif tool_name == "execute_group_chat":
                try:
                    agents = []
                    for name in tool_args["agents"]:
                        agent = self.agent_manager.get_agent(name)
                        if not agent:
                            return {"error": f"Agent {name} not found"}
                        agents.append(agent)

                    group_chat = self.agent_manager.create_group_chat(
                        agents=agents,
                        messages=[{"role": "user", "content": tool_args["message"]}],
                        max_round=10
                    )

                    manager = GroupChatManager(
                        groupchat=group_chat,
                        llm_config=self.server_config.get_default_llm_config()
                    )

                    manager.initiate_chat(tool_args["message"])

                    return {
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "agents": tool_args["agents"],
                                "messages": group_chat.messages
                            })
                        }]
                    }
                except Exception as e:
                    return {"error": str(e)}

            return {"error": f"Unknown tool: {tool_name}"}

        return {"error": f"Unknown method: {method}"}

    async def run(self):
        """Run the server using stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)

def main():
    """Run the server."""
    server = AutoGenServer()
    anyio.run(server.run)

if __name__ == "__main__":
    main()
