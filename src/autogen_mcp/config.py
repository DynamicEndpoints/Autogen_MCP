"""Configuration classes for AutoGen MCP."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class AgentConfig:
    """Configuration for an AutoGen agent."""
    name: str
    type: str  # 'assistant' or 'user'
    description: str = ""
    system_message: str = ""
    llm_config: Optional[Dict[str, Any]] = None
    code_execution_config: Optional[Dict[str, Any]] = None

    def to_autogen_config(self) -> Dict[str, Any]:
        """Convert to AutoGen configuration."""
        config = {
            "name": self.name,
            "human_input_mode": "NEVER",  # MCP handles input
            "max_consecutive_auto_reply": 10,  # Reasonable default
            "system_message": self.system_message or None,
            "llm_config": self.llm_config or {},
            "code_execution_config": self.code_execution_config or False,
        }

        # Add type-specific settings
        if self.type == "assistant":
            config.update({
                "is_termination_msg": lambda x: "TERMINATE" in x.get("content", ""),
            })
        elif self.type == "user":
            config.update({
                "human_input_mode": "NEVER",
                "code_execution_config": False,  # User agents don't execute code
            })

        return config

@dataclass
class ServerConfig:
    """Configuration for the AutoGen MCP server."""
    default_llm_config: Optional[Dict[str, Any]] = None
    default_code_execution_config: Optional[Dict[str, Any]] = None

    def get_default_llm_config(self) -> Dict[str, Any]:
        """Get default LLM configuration."""
        return self.default_llm_config or {
            "config_list": [{"model": "gpt-4"}],
            "temperature": 0,
        }

    def get_default_code_execution_config(self) -> Dict[str, Any]:
        """Get default code execution configuration."""
        return self.default_code_execution_config or {
            "work_dir": "workspace",
            "use_docker": False,
        }
