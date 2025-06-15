#!/usr/bin/env python3
import os
import json
import sys
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
import autogen
from autogen import (
    Agent, AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager,
    ConversableAgent, TeachableAgent, RetrieveUserProxyAgent
)
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
from autogen.agentchat.contrib.society_of_mind_agent import SocietyOfMindAgent
import mcp.types as types
from mcp import server

from .agents import AgentManager
from .config import ServerConfig, AgentConfig
from .workflows import WorkflowManager

load_dotenv()

class EnhancedAutoGenServer:
    def __init__(self):
        """Initialize the enhanced AutoGen MCP server."""
        self.config_path = os.getenv("AUTOGEN_MCP_CONFIG")
        if not self.config_path:
            # Create a default config if not specified
            self.config = {
                "llm_config": {
                    "config_list": [
                        {
                            "model": "gpt-4o",
                            "api_key": os.getenv("OPENAI_API_KEY")
                        }
                    ],
                    "temperature": 0.7
                },
                "code_execution_config": {
                    "work_dir": "coding",
                    "use_docker": False
                }
            }
        else:
            with open(self.config_path) as f:
                self.config = json.load(f)

        self.server_config = ServerConfig(
            default_llm_config=self.config.get("llm_config"),
            default_code_execution_config=self.config.get("code_execution_config")
        )
        self.agent_manager = AgentManager()
        self.workflow_manager = WorkflowManager()
        self.chat_history = []
        self.resource_cache = {}
        
        # Enhanced capabilities
        self.capabilities = {
            "tools": True,
            "prompts": True,
            "resources": True,
            "sampling": False  # Can be enabled if needed
        }    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls with enhanced AutoGen features."""
        try:
            if tool_name == "create_agent":
                return await self._create_agent(arguments)
            elif tool_name == "create_workflow":
                return await self._create_workflow(arguments)
            elif tool_name == "execute_chat":
                return await self._execute_chat(arguments)
            elif tool_name == "execute_group_chat":
                return await self._execute_group_chat(arguments)
            elif tool_name == "execute_nested_chat":
                return await self._execute_nested_chat(arguments)
            elif tool_name == "execute_swarm":
                return await self._execute_swarm(arguments)
            elif tool_name == "execute_workflow":
                return await self._execute_workflow(arguments)
            elif tool_name == "manage_agent_memory":
                return await self._manage_agent_memory(arguments)
            elif tool_name == "configure_teachability":
                return await self._configure_teachability(arguments)
            elif tool_name == "get_agent_status":
                return await self._get_agent_status(arguments)
            elif tool_name == "get_resource":
                return await self._get_resource(arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    async def _create_agent(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create an enhanced AutoGen agent."""
        name = args["name"]
        agent_type = args["type"]
        system_message = args.get("system_message", "You are a helpful AI assistant.")
        llm_config = args.get("llm_config", self.server_config.default_llm_config)
        code_execution_config = args.get("code_execution_config", self.server_config.default_code_execution_config)
        human_input_mode = args.get("human_input_mode", "NEVER")
        tools = args.get("tools", [])
        teachability_config = args.get("teachability", {})

        try:
            if agent_type == "assistant":
                agent = AssistantAgent(
                    name=name,
                    system_message=system_message,
                    llm_config=llm_config,
                    human_input_mode=human_input_mode,
                )
            elif agent_type == "user_proxy":
                agent = UserProxyAgent(
                    name=name,
                    system_message=system_message,
                    code_execution_config=code_execution_config,
                    human_input_mode=human_input_mode,
                )
            elif agent_type == "conversable":
                agent = ConversableAgent(
                    name=name,
                    system_message=system_message,
                    llm_config=llm_config,
                    human_input_mode=human_input_mode,
                )
            elif agent_type == "teachable":
                agent = TeachableAgent(
                    name=name,
                    system_message=system_message,
                    llm_config=llm_config,
                    teach_config=teachability_config,
                )
            elif agent_type == "retrievable":
                agent = RetrieveUserProxyAgent(
                    name=name,
                    system_message=system_message,
                    code_execution_config=code_execution_config,
                    retrieve_config=args.get("retrieve_config", {}),
                )
            else:
                return {"error": f"Unknown agent type: {agent_type}"}

            # Register tools if provided
            if tools:
                for tool in tools:
                    agent.register_for_execution(name=tool["name"])(tool["function"])

            self.agent_manager.add_agent(name, agent)
            
            return {
                "success": True,
                "message": f"Agent '{name}' created successfully",
                "agent_info": {
                    "name": name,
                    "type": agent_type,
                    "capabilities": {
                        "llm_enabled": hasattr(agent, "llm_config") and agent.llm_config is not None,
                        "code_execution": hasattr(agent, "code_execution_config") and agent.code_execution_config is not False,
                        "teachable": agent_type == "teachable",
                        "tools_count": len(tools)
                    }
                }
            }
        except Exception as e:
            return {"error": f"Failed to create agent: {str(e)}"}

    async def _create_workflow(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a complete multi-agent workflow."""
        workflow_name = args["workflow_name"]
        workflow_type = args["workflow_type"]
        agents_config = args["agents"]
        task_description = args["task_description"]
        max_rounds = args.get("max_rounds", 10)
        termination_conditions = args.get("termination_conditions", ["TERMINATE"])

        try:
            # Create agents for the workflow
            created_agents = []
            for agent_config in agents_config:
                agent_result = await self._create_agent(agent_config)
                if agent_result.get("success"):
                    created_agents.append(agent_config["name"])

            # Store workflow configuration
            workflow_config = {
                "name": workflow_name,
                "type": workflow_type,
                "agents": created_agents,
                "task": task_description,
                "max_rounds": max_rounds,
                "termination_conditions": termination_conditions,
                "created_at": datetime.now().isoformat()
            }
            
            self.workflow_manager.add_workflow(workflow_name, workflow_config)
            
            return {
                "success": True,
                "message": f"Workflow '{workflow_name}' created with {len(created_agents)} agents",
                "workflow_info": workflow_config
            }
        except Exception as e:
            return {"error": f"Failed to create workflow: {str(e)}"}

    async def _execute_chat(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an enhanced chat between two agents."""
        initiator_name = args["initiator"]
        responder_name = args["responder"]
        message = args["message"]
        max_turns = args.get("max_turns", 10)
        clear_history = args.get("clear_history", False)
        summary_method = args.get("summary_method", "last_msg")

        try:
            initiator = self.agent_manager.get_agent(initiator_name)
            responder = self.agent_manager.get_agent(responder_name)
            
            if not initiator or not responder:
                return {"error": "One or both agents not found"}

            if clear_history:
                initiator.clear_history()
                responder.clear_history()

            # Execute the chat
            chat_result = initiator.initiate_chat(
                responder, 
                message=message, 
                max_turns=max_turns,
                summary_method=summary_method
            )
            
            # Store chat history
            chat_record = {
                "timestamp": datetime.now().isoformat(),
                "initiator": initiator_name,
                "responder": responder_name,
                "initial_message": message,
                "result": chat_result,
                "turns": max_turns
            }
            self.chat_history.append(chat_record)
            
            return {
                "success": True,
                "chat_result": chat_result,
                "summary": chat_result.summary if hasattr(chat_result, 'summary') else "Chat completed",
                "cost": chat_result.cost if hasattr(chat_result, 'cost') else None
            }
        except Exception as e:
            return {"error": f"Chat execution failed: {str(e)}"}

    async def _execute_group_chat(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an enhanced group chat."""
        agent_names = args["agent_names"]
        initiator_name = args["initiator"]
        message = args["message"]
        max_round = args.get("max_round", 10)
        speaker_selection_method = args.get("speaker_selection_method", "auto")
        allow_repeat_speaker = args.get("allow_repeat_speaker", True)
        admin_name = args.get("admin_name", "Admin")

        try:
            agents = []
            for name in agent_names:
                agent = self.agent_manager.get_agent(name)
                if agent:
                    agents.append(agent)
                else:
                    return {"error": f"Agent '{name}' not found"}

            initiator = self.agent_manager.get_agent(initiator_name)
            if not initiator:
                return {"error": f"Initiator agent '{initiator_name}' not found"}

            # Create group chat with enhanced features
            group_chat = GroupChat(
                agents=agents,
                messages=[],
                max_round=max_round,
                speaker_selection_method=speaker_selection_method,
                allow_repeat_speaker=allow_repeat_speaker,
                admin_name=admin_name
            )

            manager = GroupChatManager(
                groupchat=group_chat,
                llm_config=self.server_config.default_llm_config
            )

            # Execute group chat
            chat_result = initiator.initiate_chat(manager, message=message)
            
            # Store chat history
            chat_record = {
                "timestamp": datetime.now().isoformat(),
                "type": "group_chat",
                "agents": agent_names,
                "initiator": initiator_name,
                "initial_message": message,
                "result": chat_result,
                "rounds": max_round
            }
            self.chat_history.append(chat_record)
            
            return {
                "success": True,
                "chat_result": chat_result,
                "participants": agent_names,
                "total_messages": len(group_chat.messages)
            }
        except Exception as e:
            return {"error": f"Group chat execution failed: {str(e)}"}

    async def _execute_nested_chat(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute nested conversations with hierarchical structures."""
        primary_agent_name = args["primary_agent"]
        secondary_agent_names = args["secondary_agents"]
        task = args["task"]
        max_turns = args.get("max_turns", 5)
        nesting_depth = args.get("nesting_depth", 2)

        try:
            primary_agent = self.agent_manager.get_agent(primary_agent_name)
            if not primary_agent:
                return {"error": f"Primary agent '{primary_agent_name}' not found"}

            secondary_agents = []
            for name in secondary_agent_names:
                agent = self.agent_manager.get_agent(name)
                if agent:
                    secondary_agents.append(agent)
                else:
                    return {"error": f"Secondary agent '{name}' not found"}

            # Implementation would depend on specific nested chat requirements
            # This is a simplified version
            nested_results = []
            
            for depth in range(nesting_depth):
                for secondary_agent in secondary_agents:
                    nested_task = f"Depth {depth + 1}: {task}"
                    result = primary_agent.initiate_chat(
                        secondary_agent,
                        message=nested_task,
                        max_turns=max_turns
                    )
                    nested_results.append({
                        "depth": depth + 1,
                        "secondary_agent": secondary_agent.name,
                        "result": result
                    })

            return {
                "success": True,
                "nested_results": nested_results,
                "total_conversations": len(nested_results)
            }
        except Exception as e:
            return {"error": f"Nested chat execution failed: {str(e)}"}

    async def _execute_swarm(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a swarm-based multi-agent conversation."""
        # This would be implemented based on specific swarm requirements
        # For now, return a placeholder implementation
        return {
            "success": True,
            "message": "Swarm execution not yet fully implemented",
            "placeholder": True
        }

    async def _execute_workflow(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a predefined workflow."""
        workflow_name = args["workflow_name"]
        input_data = args["input_data"]
        output_format = args.get("output_format", "json")
        quality_checks = args.get("quality_checks", False)

        try:
            result = await self.workflow_manager.execute_workflow(
                workflow_name, input_data, output_format, quality_checks
            )
            return {
                "success": True,
                "workflow": workflow_name,
                "result": result,
                "format": output_format
            }
        except Exception as e:
            return {"error": f"Workflow execution failed: {str(e)}"}

    async def _manage_agent_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Manage agent memory and knowledge persistence."""
        agent_name = args["agent_name"]
        action = args["action"]
        memory_type = args.get("memory_type", "conversation")
        
        try:
            agent = self.agent_manager.get_agent(agent_name)
            if not agent:
                return {"error": f"Agent '{agent_name}' not found"}

            if action == "save":
                # Save memory data
                data = args.get("data", {})
                # Implementation depends on agent type and memory system
                return {"success": True, "message": f"Memory saved for {agent_name}"}
            elif action == "load":
                # Load memory data
                return {"success": True, "memory_data": {}, "message": f"Memory loaded for {agent_name}"}
            elif action == "clear":
                # Clear memory
                if hasattr(agent, 'clear_history'):
                    agent.clear_history()
                return {"success": True, "message": f"Memory cleared for {agent_name}"}
            elif action == "query":
                # Query memory
                query = args.get("query", "")
                return {"success": True, "query_result": [], "message": f"Memory queried for {agent_name}"}
            else:
                return {"error": f"Unknown memory action: {action}"}
        except Exception as e:
            return {"error": f"Memory management failed: {str(e)}"}

    async def _configure_teachability(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Configure teachability features for agents."""
        agent_name = args["agent_name"]
        enable_teachability = args["enable_teachability"]
        
        try:
            agent = self.agent_manager.get_agent(agent_name)
            if not agent:
                return {"error": f"Agent '{agent_name}' not found"}

            # Implementation would depend on the specific teachability requirements
            return {
                "success": True,
                "message": f"Teachability {'enabled' if enable_teachability else 'disabled'} for {agent_name}",
                "teachability_enabled": enable_teachability
            }
        except Exception as e:
            return {"error": f"Teachability configuration failed: {str(e)}"}

    async def _get_agent_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed status and metrics for agents."""
        agent_name = args.get("agent_name")
        include_metrics = args.get("include_metrics", False)
        include_memory = args.get("include_memory", False)

        try:
            if agent_name:
                agent = self.agent_manager.get_agent(agent_name)
                if not agent:
                    return {"error": f"Agent '{agent_name}' not found"}
                agents = {agent_name: agent}
            else:
                agents = self.agent_manager.get_all_agents()

            status_data = {}
            for name, agent in agents.items():
                status = {
                    "name": name,
                    "type": type(agent).__name__,
                    "active": True,
                    "capabilities": {
                        "llm_enabled": hasattr(agent, "llm_config") and agent.llm_config is not None,
                        "code_execution": hasattr(agent, "code_execution_config") and agent.code_execution_config is not False,
                    }
                }
                
                if include_metrics:
                    status["metrics"] = {
                        "total_messages": len(getattr(agent, "chat_messages", {})),
                        "conversations": 0  # Would need to track this
                    }
                
                if include_memory:
                    status["memory"] = {
                        "history_length": len(getattr(agent, "chat_messages", {})),
                        "memory_size": 0  # Would need to calculate this
                    }
                
                status_data[name] = status

            return {
                "success": True,
                "agents": status_data,
                "total_agents": len(status_data)
            }
        except Exception as e:
            return {"error": f"Status retrieval failed: {str(e)}"}

    async def _get_resource(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get resource data for MCP resources."""
        uri = args["uri"]
        
        try:
            if uri == "autogen://agents/list":
                agents = self.agent_manager.get_all_agents()
                agent_list = []
                for name, agent in agents.items():
                    agent_list.append({
                        "name": name,
                        "type": type(agent).__name__,
                        "status": "active"
                    })
                return {"agents": agent_list}
            
            elif uri == "autogen://chat/history":
                # Return recent chat history
                recent_history = self.chat_history[-10:]  # Last 10 chats
                history_text = ""
                for chat in recent_history:
                    history_text += f"[{chat['timestamp']}] {chat['initiator']} -> {chat.get('responder', 'Group')}: {chat['initial_message'][:100]}...\n"
                return {"content": history_text}
            
            elif uri == "autogen://config/current":
                return {
                    "llm_config": self.server_config.default_llm_config,
                    "code_execution_config": self.server_config.default_code_execution_config,
                    "capabilities": self.capabilities
                }
            
            else:
                return {"error": f"Unknown resource URI: {uri}"}
                
        except Exception as e:
            return {"error": f"Resource retrieval failed: {str(e)}"}

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
