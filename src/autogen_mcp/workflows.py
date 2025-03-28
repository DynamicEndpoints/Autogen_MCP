"""Workflow management for AutoGen MCP."""

from typing import Dict, List, Optional, Sequence, Any, cast
import autogen
from autogen import ConversableAgent, Agent, GroupChat, GroupChatManager
from .agents import AgentManager
from .config import AgentConfig, ServerConfig

class WorkflowManager:
    """Manages AutoGen workflows."""

    def __init__(self, agent_manager: AgentManager):
        """Initialize the workflow manager."""
        self._agent_manager = agent_manager

    async def execute_chat(
        self,
        initiator: str,
        responder: str,
        message: str,
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a simple chat between two agents."""
        initiator_agent = self._agent_manager.get_agent(initiator)
        responder_agent = self._agent_manager.get_agent(responder)

        if not initiator_agent or not responder_agent:
            raise ValueError("Invalid agent names")

        # Initialize chat history
        chat_history = []

        # Create a function to capture messages
        def capture_message(sender: ConversableAgent, message: Dict[str, Any]) -> None:
            chat_history.append({
                "role": sender.name,
                "content": message.get("content", ""),
            })

        # Register message handlers
        initiator_agent.register_reply(
            responder_agent,
            lambda sender, message: capture_message(sender, message)
        )
        responder_agent.register_reply(
            initiator_agent,
            lambda sender, message: capture_message(sender, message)
        )

        # Start the chat
        try:
            await initiator_agent.a_initiate_chat(
                responder_agent,
                message=message,
                llm_config=llm_config,
            )
        finally:
            # Clean up message handlers
            initiator_agent.reset_consecutive_auto_reply_counter()
            responder_agent.reset_consecutive_auto_reply_counter()

        return chat_history

    async def execute_group_chat(
        self,
        agent_names: Sequence[str],
        initiator: str,
        message: str,
        max_round: int = 10,
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a group chat with multiple agents."""
        agents = []
        for name in agent_names:
            agent = self._agent_manager.get_agent(name)
            if not agent:
                raise ValueError(f"Invalid agent name: {name}")
            agents.append(agent)

        initiator_agent = self._agent_manager.get_agent(initiator)
        if not initiator_agent:
            raise ValueError(f"Invalid initiator agent: {initiator}")

        # Create group chat
        groupchat = GroupChat(
            agents=cast(List[Agent], agents),
            messages=[],
            max_round=max_round,
        )
        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config=llm_config,
        )

        # Initialize chat history
        chat_history = []

        # Create a function to capture messages
        def capture_message(sender: ConversableAgent, message: Dict[str, Any]) -> None:
            chat_history.append({
                "role": sender.name,
                "content": message.get("content", ""),
            })

        # Register message handlers for all agents
        for agent in agents:
            agent.register_reply(
                manager,
                lambda sender, message: capture_message(sender, message)
            )

        # Start the chat
        try:
            await initiator_agent.a_initiate_chat(
                manager,
                message=message,
                llm_config=llm_config,
            )
        finally:
            # Clean up message handlers
            for agent in agents:
                agent.reset_consecutive_auto_reply_counter()

        return chat_history

    async def execute_workflow(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a predefined workflow."""
        if workflow_name == "code_generation":
            return await self._code_generation_workflow(input_data, llm_config)
        elif workflow_name == "research":
            return await self._research_workflow(input_data, llm_config)
        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")

    async def _code_generation_workflow(
        self,
        input_data: Dict[str, Any],
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute code generation workflow."""
        # Create necessary agents
        user_proxy = self._agent_manager.get_agent("user")
        assistant = self._agent_manager.get_agent("assistant")
        if not user_proxy or not assistant:
            raise ValueError("Required agents not found")

        # Execute the workflow
        chat_history = await self.execute_chat(
            initiator="user",
            responder="assistant",
            message=input_data.get("prompt", ""),
            llm_config=llm_config,
        )

        # Extract generated code from chat history
        code_blocks = []
        for msg in chat_history:
            if msg.get("role") == "assistant" and msg.get("content"):
                content = msg["content"]
                if "```" in content:
                    code = content.split("```")[1]
                    code_blocks.append(code)

        return {
            "chat_history": chat_history,
            "generated_code": code_blocks,
        }

    async def _research_workflow(
        self,
        input_data: Dict[str, Any],
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute research workflow."""
        # Create a group of agents for research
        researcher = self._agent_manager.get_agent("researcher")
        critic = self._agent_manager.get_agent("critic")
        writer = self._agent_manager.get_agent("writer")
        if not all([researcher, critic, writer]):
            raise ValueError("Required agents not found")

        # Execute the workflow
        chat_history = await self.execute_group_chat(
            agent_names=["researcher", "critic", "writer"],
            initiator="researcher",
            message=input_data.get("topic", ""),
            max_round=5,
            llm_config=llm_config,
        )

        # Extract research findings
        findings = []
        for msg in chat_history:
            if msg.get("role") == "writer" and msg.get("content"):
                findings.append(msg["content"])

        return {
            "chat_history": chat_history,
            "findings": findings,
        }
