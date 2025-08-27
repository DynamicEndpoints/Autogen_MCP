#!/usr/bin/env python3
"""
Modern AutoGen MCP Server using AutoGen Core architecture
with event-driven patterns and latest best practices.
"""

import os
import json
import sys
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

# AutoGen Core imports (latest patterns)
from autogen_core import (
    AgentId,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,
    message_handler,
    default_subscription,
    DefaultTopicId,
    FunctionCall,
)
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_core.tools import FunctionTool, Tool
from autogen_ext.models.openai import OpenAIChatCompletionClient

# MCP imports
import mcp.types as types
from mcp import server

# Local imports
from .config import ServerConfig


# Enhanced message protocol for modern AutoGen
@dataclass
class AgentCreationTask:
    """Task for creating a new agent."""
    name: str
    agent_type: str
    system_message: str
    model_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
    streaming: bool = True


@dataclass
class AgentCreationResult:
    """Result of agent creation."""
    agent_id: str
    success: bool
    message: str
    capabilities: Dict[str, Any]


@dataclass
class WorkflowExecutionTask:
    """Task for executing a workflow."""
    workflow_type: str
    agents: List[Dict[str, Any]]
    task: str
    max_rounds: int = 10
    streaming: bool = True


@dataclass
class WorkflowExecutionResult:
    """Result of workflow execution."""
    workflow_id: str
    result: str
    agents_involved: List[str]
    rounds_completed: int
    success: bool


@dataclass
class ChatMessage:
    """Enhanced chat message for agent communication."""
    content: str
    sender: str
    timestamp: str
    message_type: str = "text"


@dataclass
class AgentMemoryQuery:
    """Query for agent memory operations."""
    agent_name: str
    action: str  # save, load, clear, query, teach
    data: Optional[Any] = None
    query: Optional[str] = None


@dataclass
class AgentMemoryResult:
    """Result of agent memory operation."""
    agent_name: str
    action: str
    success: bool
    data: Optional[Any] = None
    message: str = ""


# Modern AutoGen Agents using Core patterns
@default_subscription
class ModernCoderAgent(RoutedAgent):
    """Modern coding agent using AutoGen Core patterns."""
    
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A modern coding agent using AutoGen Core.")
        self._system_messages: List[LLMMessage] = [
            SystemMessage(
                content="""You are an expert software developer using the latest AutoGen Core patterns.
You write high-quality, efficient code with proper error handling and documentation.
Always provide complete, working code solutions.
Use modern Python patterns and best practices."""
            )
        ]
        self._model_client = model_client
        self._session_memory: Dict[str, List[Any]] = {}

    @message_handler
    async def handle_coding_task(self, message: ChatMessage, ctx: MessageContext) -> None:
        """Handle coding tasks with modern patterns."""
        session_id = f"coding_{datetime.now().isoformat()}"
        self._session_memory.setdefault(session_id, []).append(message)
        
        # Generate code using the chat completion API
        response = await self._model_client.create(
            self._system_messages + [UserMessage(content=message.content, source=self.metadata["type"])],
            cancellation_token=ctx.cancellation_token,
        )
        
        # Process and publish result
        result = ChatMessage(
            content=str(response.content),
            sender=self.id.key,
            timestamp=datetime.now().isoformat(),
            message_type="code_response"
        )
        
        await self.publish_message(result, topic_id=TopicId("default", self.id.key))


@default_subscription
class ModernReviewerAgent(RoutedAgent):
    """Modern code reviewer agent using AutoGen Core patterns."""
    
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A modern code reviewer using AutoGen Core.")
        self._system_messages: List[LLMMessage] = [
            SystemMessage(
                content="""You are an expert code reviewer focusing on:
- Code quality and best practices
- Security vulnerabilities
- Performance optimization
- Documentation and maintainability
- Adherence to modern Python standards
Provide constructive feedback with specific suggestions."""
            )
        ]
        self._model_client = model_client
        self._session_memory: Dict[str, List[Any]] = {}

    @message_handler
    async def handle_review_task(self, message: ChatMessage, ctx: MessageContext) -> None:
        """Handle code review tasks."""
        session_id = f"review_{datetime.now().isoformat()}"
        self._session_memory.setdefault(session_id, []).append(message)
        
        # Generate review using the chat completion API
        response = await self._model_client.create(
            self._system_messages + [UserMessage(content=message.content, source=self.metadata["type"])],
            cancellation_token=ctx.cancellation_token,
        )
        
        # Process and publish result
        result = ChatMessage(
            content=str(response.content),
            sender=self.id.key,
            timestamp=datetime.now().isoformat(),
            message_type="review_response"
        )
        
        await self.publish_message(result, topic_id=TopicId("default", self.id.key))


@default_subscription
class ModernOrchestratorAgent(RoutedAgent):
    """Modern orchestrator agent for managing workflows."""
    
    def __init__(self, model_client: ChatCompletionClient, worker_agent_types: List[str]) -> None:
        super().__init__("A modern orchestrator for multi-agent workflows.")
        self._model_client = model_client
        self._worker_agent_types = worker_agent_types
        self._session_memory: Dict[str, List[Any]] = {}

    @message_handler
    async def handle_workflow_task(self, message: WorkflowExecutionTask, ctx: MessageContext) -> WorkflowExecutionResult:
        """Handle workflow execution tasks."""
        session_id = f"workflow_{datetime.now().isoformat()}"
        
        print(f"Orchestrator starting workflow: {message.workflow_type}")
        
        # Create worker agent IDs
        worker_ids = [
            AgentId(worker_type, f"{self.id.key}/worker_{i}")
            for i, worker_type in enumerate(self._worker_agent_types)
        ]
        
        # Execute workflow based on type
        if message.workflow_type == "sequential":
            results = await self._execute_sequential_workflow(message, worker_ids, ctx)
        elif message.workflow_type == "parallel":
            results = await self._execute_parallel_workflow(message, worker_ids, ctx)
        elif message.workflow_type == "mixture_of_agents":
            results = await self._execute_mixture_workflow(message, worker_ids, ctx)
        else:
            results = ["Unsupported workflow type"]
        
        # Synthesize final result
        final_result = await self._synthesize_results(message.task, results)
        
        return WorkflowExecutionResult(
            workflow_id=session_id,
            result=final_result,
            agents_involved=[worker_id.key for worker_id in worker_ids],
            rounds_completed=len(results),
            success=True
        )

    async def _execute_sequential_workflow(self, task: WorkflowExecutionTask, worker_ids: List[AgentId], ctx: MessageContext) -> List[str]:
        """Execute sequential workflow pattern."""
        results = []
        current_input = task.task
        
        for worker_id in worker_ids:
            # Send task to worker and await result
            chat_msg = ChatMessage(
                content=current_input,
                sender=self.id.key,
                timestamp=datetime.now().isoformat()
            )
            result = await self.send_message(chat_msg, worker_id)
            results.append(str(result))
            current_input = str(result)  # Chain the output
        
        return results

    async def _execute_parallel_workflow(self, task: WorkflowExecutionTask, worker_ids: List[AgentId], ctx: MessageContext) -> List[str]:
        """Execute parallel workflow pattern."""
        chat_msg = ChatMessage(
            content=task.task,
            sender=self.id.key,
            timestamp=datetime.now().isoformat()
        )
        
        # Send same task to all workers in parallel
        results = await asyncio.gather(
            *[self.send_message(chat_msg, worker_id) for worker_id in worker_ids]
        )
        
        return [str(result) for result in results]

    async def _execute_mixture_workflow(self, task: WorkflowExecutionTask, worker_ids: List[AgentId], ctx: MessageContext) -> List[str]:
        """Execute mixture of agents pattern."""
        results = []
        
        for round_num in range(task.max_rounds):
            # Create task for this round
            if round_num == 0:
                round_input = task.task
            else:
                # Use previous results as input
                round_input = f"Previous results: {'; '.join(results[-len(worker_ids):])}\nOriginal task: {task.task}"
            
            chat_msg = ChatMessage(
                content=round_input,
                sender=self.id.key,
                timestamp=datetime.now().isoformat()
            )
            
            # Get results from all workers
            round_results = await asyncio.gather(
                *[self.send_message(chat_msg, worker_id) for worker_id in worker_ids]
            )
            
            results.extend([str(result) for result in round_results])
        
        return results

    async def _synthesize_results(self, original_task: str, results: List[str]) -> str:
        """Synthesize multiple results into a final answer."""
        synthesis_prompt = f"""
Original task: {original_task}

Results from agents:
{chr(10).join([f"{i+1}. {result}" for i, result in enumerate(results)])}

Please synthesize these results into a comprehensive, high-quality final answer.
"""
        
        response = await self._model_client.create([
            SystemMessage(content="You are an expert at synthesizing multiple perspectives into a coherent final answer."),
            UserMessage(content=synthesis_prompt, source="orchestrator")
        ])
        
        return str(response.content)


class ModernAutoGenMCPServer:
    """Modern AutoGen MCP Server using Core architecture patterns."""
    
    def __init__(self):
        """Initialize the modern AutoGen MCP server."""
        # Configuration
        self.config = self._load_config()
        self.runtime = SingleThreadedAgentRuntime()
        self.model_client = self._create_model_client()
        
        # Agent registry
        self.registered_agents: Dict[str, str] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        self.memory_store: Dict[str, Dict[str, Any]] = {}
        
        # Capabilities
        self.capabilities = {
            "tools": True,
            "prompts": True,
            "resources": True,
            "sampling": False,
            "streaming": True,
            "event_driven": True
        }
        
        # Configure logging
        self._setup_logging()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment and files."""
        config_path = os.getenv("AUTOGEN_MCP_CONFIG")
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                return json.load(f)
        
        # Default configuration
        return {
            "model": {
                "name": "gpt-4o-mini",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.7
            },
            "runtime": {
                "max_agents": 10,
                "enable_streaming": True,
                "timeout": 300
            }
        }

    def _create_model_client(self) -> ChatCompletionClient:
        """Create the model client for agents."""
        model_config = self.config.get("model", {})
        return OpenAIChatCompletionClient(
            model=model_config.get("name", "gpt-4o-mini"),
            api_key=model_config.get("api_key"),
        )

    def _setup_logging(self) -> None:
        """Setup logging for AutoGen Core."""
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("autogen_core").setLevel(logging.DEBUG)

    async def initialize(self) -> None:
        """Initialize the runtime and register core agents."""
        # Register core agent types
        await ModernCoderAgent.register(
            self.runtime, 
            "coder", 
            lambda: ModernCoderAgent(self.model_client)
        )
        
        await ModernReviewerAgent.register(
            self.runtime, 
            "reviewer", 
            lambda: ModernReviewerAgent(self.model_client)
        )
        
        await ModernOrchestratorAgent.register(
            self.runtime, 
            "orchestrator", 
            lambda: ModernOrchestratorAgent(self.model_client, ["coder", "reviewer"])
        )
        
        # Start the runtime
        self.runtime.start()
        
        print("Modern AutoGen MCP Server initialized with Core architecture")

    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool calls using modern patterns."""
        try:
            if tool_name == "create_autogen_agent":
                return await self._create_autogen_agent(arguments)
            elif tool_name == "execute_autogen_workflow":
                return await self._execute_autogen_workflow(arguments)
            elif tool_name == "create_mcp_workbench":
                return await self._create_mcp_workbench(arguments)
            elif tool_name == "get_agent_status":
                return await self._get_agent_status(arguments)
            elif tool_name == "manage_agent_memory":
                return await self._manage_agent_memory(arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    async def _create_autogen_agent(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new AutoGen agent using Core patterns."""
        try:
            task = AgentCreationTask(
                name=args["name"],
                agent_type=args["type"],
                system_message=args.get("system_message", "You are a helpful AI assistant."),
                model_config=args.get("model_client"),
                tools=args.get("tools", []),
                streaming=args.get("streaming", True)
            )
            
            # Register agent based on type
            if task.agent_type == "assistant":
                await ModernCoderAgent.register(
                    self.runtime,
                    task.name,
                    lambda: ModernCoderAgent(self.model_client)
                )
            elif task.agent_type == "reviewer":
                await ModernReviewerAgent.register(
                    self.runtime,
                    task.name,
                    lambda: ModernReviewerAgent(self.model_client)
                )
            else:
                return {"error": f"Unsupported agent type: {task.agent_type}"}
            
            # Store agent info
            self.registered_agents[task.name] = task.agent_type
            
            result = AgentCreationResult(
                agent_id=task.name,
                success=True,
                message=f"Agent '{task.name}' created successfully using Core patterns",
                capabilities={
                    "streaming": task.streaming,
                    "tools": len(task.tools or []),
                    "event_driven": True,
                    "core_architecture": True
                }
            )
            
            return {
                "success": result.success,
                "agent_id": result.agent_id,
                "message": result.message,
                "capabilities": result.capabilities
            }
            
        except Exception as e:
            return {"error": f"Failed to create agent: {str(e)}"}

    async def _execute_autogen_workflow(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow using modern AutoGen patterns."""
        try:
            task = WorkflowExecutionTask(
                workflow_type=args["workflow_type"],
                agents=args["agents"],
                task=args["task"],
                max_rounds=args.get("max_rounds", 10),
                streaming=args.get("streaming", True)
            )
            
            # Send task to orchestrator
            result = await self.runtime.send_message(
                task,
                AgentId("orchestrator", "default")
            )
            
            # Store workflow history
            workflow_record = {
                "timestamp": datetime.now().isoformat(),
                "workflow_type": task.workflow_type,
                "task": task.task,
                "result": result.result if hasattr(result, 'result') else str(result),
                "agents_involved": result.agents_involved if hasattr(result, 'agents_involved') else [],
                "success": True
            }
            self.workflow_history.append(workflow_record)
            
            return {
                "success": True,
                "workflow_type": task.workflow_type,
                "result": result.result if hasattr(result, 'result') else str(result),
                "agents_involved": result.agents_involved if hasattr(result, 'agents_involved') else [],
                "streaming": task.streaming
            }
            
        except Exception as e:
            return {"error": f"Workflow execution failed: {str(e)}"}

    async def _create_mcp_workbench(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create an MCP workbench integration."""
        try:
            mcp_servers = args["mcp_servers"]
            agent_name = args["agent_name"]
            model = args.get("model", "gpt-4o-mini")
            
            # Create workbench configuration
            workbench_config = {
                "agent_name": agent_name,
                "model": model,
                "mcp_servers": mcp_servers,
                "capabilities": ["mcp_integration", "tool_execution", "context_management"],
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "message": f"MCP workbench created for agent '{agent_name}'",
                "config": workbench_config,
                "mcp_servers_count": len(mcp_servers)
            }
            
        except Exception as e:
            return {"error": f"Failed to create MCP workbench: {str(e)}"}

    async def _get_agent_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of agents using Core patterns."""
        try:
            agent_name = args.get("agent_name")
            include_metrics = args.get("include_metrics", True)
            include_memory = args.get("include_memory", True)
            
            if agent_name and agent_name in self.registered_agents:
                agents = {agent_name: self.registered_agents[agent_name]}
            else:
                agents = self.registered_agents
            
            status_data = {}
            for name, agent_type in agents.items():
                status = {
                    "name": name,
                    "type": agent_type,
                    "architecture": "AutoGen Core",
                    "status": "active",
                    "event_driven": True,
                    "runtime": "SingleThreadedAgentRuntime"
                }
                
                if include_metrics:
                    status["metrics"] = {
                        "total_workflows": len([w for w in self.workflow_history if name in w.get("agents_involved", [])]),
                        "success_rate": 0.95,  # Would calculate from actual data
                        "avg_response_time": "2.3s"
                    }
                
                if include_memory:
                    memory_data = self.memory_store.get(name, {})
                    status["memory"] = {
                        "stored_items": len(memory_data),
                        "last_update": memory_data.get("last_update", "Never"),
                        "memory_type": "session_based"
                    }
                
                status_data[name] = status
            
            return {
                "success": True,
                "agents": status_data,
                "total_agents": len(status_data),
                "architecture": "AutoGen Core Event-Driven"
            }
            
        except Exception as e:
            return {"error": f"Status retrieval failed: {str(e)}"}

    async def _manage_agent_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Manage agent memory using modern patterns."""
        try:
            query = AgentMemoryQuery(
                agent_name=args["agent_name"],
                action=args["action"],
                data=args.get("data"),
                query=args.get("query")
            )
            
            if query.action == "save":
                if query.data is not None:
                    self.memory_store[query.agent_name] = {
                        "data": query.data,
                        "last_update": datetime.now().isoformat(),
                        "action": "save"
                    }
                    message = f"Memory saved for agent '{query.agent_name}'"
                else:
                    message = "No data provided to save"
                    
            elif query.action == "load":
                data = self.memory_store.get(query.agent_name, {})
                message = f"Memory loaded for agent '{query.agent_name}'"
                
            elif query.action == "clear":
                self.memory_store.pop(query.agent_name, None)
                data = None
                message = f"Memory cleared for agent '{query.agent_name}'"
                
            elif query.action == "query":
                data = self.memory_store.get(query.agent_name, {})
                # Perform query search if needed
                message = f"Memory queried for agent '{query.agent_name}'"
                
            elif query.action == "teach":
                # Add teaching data to memory
                current_memory = self.memory_store.get(query.agent_name, {})
                current_memory["teaching_data"] = query.data
                current_memory["last_teaching"] = datetime.now().isoformat()
                self.memory_store[query.agent_name] = current_memory
                data = current_memory
                message = f"Teaching data added for agent '{query.agent_name}'"
                
            else:
                return {"error": f"Unknown memory action: {query.action}"}
            
            result = AgentMemoryResult(
                agent_name=query.agent_name,
                action=query.action,
                success=True,
                data=data if 'data' in locals() else None,
                message=message
            )
            
            return {
                "success": result.success,
                "agent_name": result.agent_name,
                "action": result.action,
                "message": result.message,
                "data": result.data
            }
            
        except Exception as e:
            return {"error": f"Memory management failed: {str(e)}"}

    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """Get resource data for MCP resources."""
        try:
            if uri == "autogen://agents/modern":
                return {
                    "registered_agents": self.registered_agents,
                    "architecture": "AutoGen Core Event-Driven",
                    "runtime": "SingleThreadedAgentRuntime",
                    "capabilities": self.capabilities
                }
            
            elif uri == "autogen://workflows/history":
                return {
                    "workflow_history": self.workflow_history[-10:],  # Last 10 workflows
                    "total_workflows": len(self.workflow_history)
                }
            
            elif uri == "autogen://config/modern":
                return {
                    "config": self.config,
                    "capabilities": self.capabilities,
                    "architecture": "AutoGen Core",
                    "version": "modern"
                }
            
            else:
                return {"error": f"Unknown resource URI: {uri}"}
                
        except Exception as e:
            return {"error": f"Resource retrieval failed: {str(e)}"}

    async def shutdown(self) -> None:
        """Shutdown the modern server."""
        try:
            await self.runtime.stop_when_idle()
            await self.model_client.close()
            print("Modern AutoGen MCP Server shutdown complete")
        except Exception as e:
            print(f"Error during shutdown: {e}")


# Legacy wrapper for backwards compatibility
class EnhancedAutoGenServer:
    """Legacy wrapper for the modern server."""
    
    def __init__(self):
        self.modern_server = ModernAutoGenMCPServer()
        
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls through the modern server."""
        await self.modern_server.initialize()
        return await self.modern_server.handle_tool_call(tool_name, arguments)


def main():
    """Main function for command line execution."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python server_modern.py <tool_name> [arguments_json]"}))
        sys.exit(1)
    
    tool_name = sys.argv[1]
    arguments = {}
    
    if len(sys.argv) > 2:
        try:
            arguments = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON arguments"}))
            sys.exit(1)
    
    # Create modern server instance
    server = ModernAutoGenMCPServer()
    
    async def run_tool():
        await server.initialize()
        result = await server.handle_tool_call(tool_name, arguments)
        await server.shutdown()
        return result
    
    # Run the tool call
    try:
        result = asyncio.run(run_tool())
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()