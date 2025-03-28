"""Agent management for AutoGen MCP."""

from typing import Dict, Optional, Any, List, cast
import autogen
from autogen import ConversableAgent, Agent
from .config import AgentConfig, ServerConfig

class AgentManager:
    """Manages AutoGen agents."""

    def __init__(self):
        """Initialize the agent manager."""
        self._agents: Dict[str, ConversableAgent] = {}
        self._server_config = ServerConfig()

    def create_agent(self, config: AgentConfig) -> ConversableAgent:
        """Create a new agent."""
        if config.name in self._agents:
            raise ValueError(f"Agent {config.name} already exists")

        # Get base configuration
        agent_config = config.to_autogen_config()

        # Add default configurations if not provided
        if not agent_config.get("llm_config"):
            agent_config["llm_config"] = self._server_config.get_default_llm_config()
        if not agent_config.get("code_execution_config") and config.type == "assistant":
            agent_config["code_execution_config"] = self._server_config.get_default_code_execution_config()

        # Create the appropriate agent type
        if config.type == "assistant":
            agent = autogen.AssistantAgent(
                name=config.name,
                system_message=agent_config.get("system_message", ""),
                llm_config=agent_config.get("llm_config"),
                code_execution_config=agent_config.get("code_execution_config"),
                human_input_mode="NEVER",
                max_consecutive_auto_reply=10,
            )
        elif config.type == "user":
            agent = autogen.UserProxyAgent(
                name=config.name,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=10,
                system_message=agent_config.get("system_message", ""),
                code_execution_config=False,
            )
        else:
            raise ValueError(f"Unknown agent type: {config.type}")

        self._agents[config.name] = agent
        return agent

    def get_agent(self, name: str) -> Optional[ConversableAgent]:
        """Get an agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        """List all agent names."""
        return list(self._agents.keys())

    def remove_agent(self, name: str) -> None:
        """Remove an agent."""
        if name in self._agents:
            del self._agents[name]

    def create_group_chat(
        self,
        agents: List[ConversableAgent],
        messages: Optional[List[Dict[str, Any]]] = None,
        max_round: int = 10,
    ) -> autogen.GroupChat:
        """Create a group chat."""
        return autogen.GroupChat(
            agents=cast(List[Agent], agents),
            messages=messages or [],
            max_round=max_round,
        )
