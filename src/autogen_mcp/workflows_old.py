"""Enhanced workflow management for AutoGen MCP with latest features."""

from typing import Dict, List, Optional, Sequence, Any, cast
import asyncio
import json
from datetime import datetime
import autogen
from autogen import ConversableAgent, Agent, GroupChat, GroupChatManager, AssistantAgent, UserProxyAgent
from .agents import AgentManager
from .config import AgentConfig, ServerConfig


class WorkflowManager:
    """Enhanced workflow manager with support for latest AutoGen features."""

    def __init__(self):
        """Initialize the workflow manager."""
        self._workflows = {}
        self._workflow_templates = {
            "code_generation": self._code_generation_workflow,
            "research": self._research_workflow,
            "analysis": self._analysis_workflow,
            "creative_writing": self._creative_writing_workflow,
            "problem_solving": self._problem_solving_workflow,
            "code_review": self._code_review_workflow,
        }

    def add_workflow(self, name: str, config: Dict[str, Any]) -> None:
        """Add a workflow configuration."""
        self._workflows[name] = config

    def get_workflow(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a workflow configuration."""
        return self._workflows.get(name)

    def list_workflows(self) -> List[str]:
        """List all available workflows."""
        return list(self._workflows.keys())

    async def execute_workflow(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
        output_format: str = "json",
        quality_checks: bool = False
    ) -> Dict[str, Any]:
        """Execute a predefined workflow with enhanced features."""
        if workflow_name in self._workflow_templates:
            return await self._workflow_templates[workflow_name](
                input_data, output_format, quality_checks
            )
        elif workflow_name in self._workflows:
            return await self._execute_custom_workflow(
                self._workflows[workflow_name], input_data, output_format, quality_checks
            )
        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")

    async def _code_generation_workflow(
        self, input_data: Dict[str, Any], output_format: str, quality_checks: bool
    ) -> Dict[str, Any]:
        """Enhanced code generation workflow."""
        task = input_data.get("task", "")
        language = input_data.get("language", "python")
        requirements = input_data.get("requirements", [])
        
        # Create specialized agents for code generation
        architect = AssistantAgent(
            name="architect",
            system_message=f"""You are a software architect. Design the solution for: {task}
            Language: {language}
            Requirements: {requirements}
            Provide a high-level design and structure.""",
            llm_config={"model": "gpt-4o", "temperature": 0.3}
        )
        
        developer = AssistantAgent(
            name="developer",
            system_message=f"""You are a senior developer. Implement the solution based on the architect's design.
            Write clean, efficient {language} code.
            Follow best practices and include proper error handling.""",
            llm_config={"model": "gpt-4o", "temperature": 0.2}
        )
        
        reviewer = AssistantAgent(
            name="reviewer",
            system_message=f"""You are a code reviewer. Review the generated code for:
            - Correctness and functionality
            - Code quality and best practices
            - Security considerations
            - Performance optimization
            Provide constructive feedback and suggestions.""",
            llm_config={"model": "gpt-4o", "temperature": 0.1}
        )
        
        executor = UserProxyAgent(
            name="executor",
            system_message="Execute and test the generated code.",
            code_execution_config={"work_dir": "coding", "use_docker": False},
            human_input_mode="NEVER"
        )

        # Execute the workflow
        result = {
            "workflow": "code_generation",
            "task": task,
            "language": language,
            "timestamp": datetime.now().isoformat(),
            "stages": []
        }

        # Stage 1: Architecture design
        architect_result = architect.initiate_chat(
            developer,
            message=f"Design a solution for: {task}. Language: {language}. Requirements: {requirements}",
            max_turns=3
        )
        result["stages"].append({
            "stage": "architecture",
            "result": str(architect_result)
        })

        # Stage 2: Code implementation
        if quality_checks:
            # Include reviewer in the process
            group_chat = GroupChat(
                agents=[developer, reviewer, executor],
                messages=[],
                max_round=10,
                speaker_selection_method="round_robin"
            )
            manager = GroupChatManager(groupchat=group_chat, llm_config={"model": "gpt-4o"})
            
            implementation_result = developer.initiate_chat(
                manager,
                message=f"Implement the code based on the architecture. Include testing.",
                max_turns=8
            )
        else:
            implementation_result = developer.initiate_chat(
                executor,
                message=f"Implement and test the code based on the architecture.",
                max_turns=5
            )
        
        result["stages"].append({
            "stage": "implementation",
            "result": str(implementation_result)
        })

        return result

    async def _research_workflow(
        self, input_data: Dict[str, Any], output_format: str, quality_checks: bool
    ) -> Dict[str, Any]:
        """Enhanced research workflow."""
        topic = input_data.get("topic", "")
        depth = input_data.get("depth", "detailed")
        sources = input_data.get("sources", [])
        
        # Create research team
        researcher = AssistantAgent(
            name="researcher",
            system_message=f"""You are a research specialist. Research the topic: {topic}
            Depth level: {depth}
            Focus on gathering comprehensive information from reliable sources.""",
            llm_config={"model": "gpt-4o", "temperature": 0.4}
        )
        
        analyst = AssistantAgent(
            name="analyst",
            system_message=f"""You are a data analyst. Analyze the research findings for: {topic}
            Identify patterns, trends, and key insights.
            Provide structured analysis and conclusions.""",
            llm_config={"model": "gpt-4o", "temperature": 0.3}
        )
        
        critic = AssistantAgent(
            name="critic",
            system_message=f"""You are a critical reviewer. Evaluate the research and analysis for: {topic}
            Check for biases, gaps, and inconsistencies.
            Suggest improvements and additional areas to explore.""",
            llm_config={"model": "gpt-4o", "temperature": 0.2}
        )
        
        synthesizer = AssistantAgent(
            name="synthesizer",
            system_message=f"""You are a synthesis specialist. Create a comprehensive summary of the research on: {topic}
            Integrate findings from all team members.
            Present a coherent, well-structured final report.""",
            llm_config={"model": "gpt-4o", "temperature": 0.3}
        )

        # Execute research workflow
        result = {
            "workflow": "research",
            "topic": topic,
            "depth": depth,
            "timestamp": datetime.now().isoformat(),
            "stages": []
        }

        # Stage 1: Initial research
        research_result = researcher.initiate_chat(
            analyst,
            message=f"Research the topic: {topic}. Focus on {depth} analysis.",
            max_turns=5
        )
        result["stages"].append({
            "stage": "research",
            "result": str(research_result)
        })

        # Stage 2: Analysis and critique
        if quality_checks:
            group_chat = GroupChat(
                agents=[analyst, critic, synthesizer],
                messages=[],
                max_round=8,
                speaker_selection_method="auto"
            )
            manager = GroupChatManager(groupchat=group_chat, llm_config={"model": "gpt-4o"})
            
            analysis_result = analyst.initiate_chat(
                manager,
                message="Analyze the research findings and provide critical evaluation.",
                max_turns=6
            )
        else:
            analysis_result = analyst.initiate_chat(
                synthesizer,
                message="Analyze the research findings and create a synthesis.",
                max_turns=4
            )
        
        result["stages"].append({
            "stage": "analysis",
            "result": str(analysis_result)
        })

        return result

    async def _analysis_workflow(
        self, input_data: Dict[str, Any], output_format: str, quality_checks: bool
    ) -> Dict[str, Any]:
        """Data analysis workflow."""
        # Simplified implementation
        return {
            "workflow": "analysis",
            "input": input_data,
            "result": "Analysis workflow executed",
            "format": output_format,
            "timestamp": datetime.now().isoformat()
        }

    async def _creative_writing_workflow(
        self, input_data: Dict[str, Any], output_format: str, quality_checks: bool
    ) -> Dict[str, Any]:
        """Creative writing workflow."""
        # Simplified implementation
        return {
            "workflow": "creative_writing",
            "input": input_data,
            "result": "Creative writing workflow executed",
            "format": output_format,
            "timestamp": datetime.now().isoformat()
        }

    async def _problem_solving_workflow(
        self, input_data: Dict[str, Any], output_format: str, quality_checks: bool
    ) -> Dict[str, Any]:
        """Problem solving workflow."""
        # Simplified implementation
        return {
            "workflow": "problem_solving",
            "input": input_data,
            "result": "Problem solving workflow executed",
            "format": output_format,
            "timestamp": datetime.now().isoformat()
        }

    async def _code_review_workflow(
        self, input_data: Dict[str, Any], output_format: str, quality_checks: bool
    ) -> Dict[str, Any]:
        """Code review workflow."""
        code = input_data.get("code", "")
        language = input_data.get("language", "auto-detect")
        focus_areas = input_data.get("focus_areas", ["security", "performance", "readability"])
        
        # Create review team
        security_reviewer = AssistantAgent(
            name="security_reviewer",
            system_message=f"""You are a security expert. Review this {language} code for security vulnerabilities:
            - Input validation issues
            - SQL injection risks
            - Authentication/authorization flaws
            - Data exposure risks
            Provide specific recommendations.""",
            llm_config={"model": "gpt-4o", "temperature": 0.1}
        )
        
        performance_reviewer = AssistantAgent(
            name="performance_reviewer",
            system_message=f"""You are a performance optimization expert. Review this {language} code for:
            - Algorithm efficiency
            - Memory usage
            - Database query optimization
            - Scalability issues
            Suggest specific improvements.""",
            llm_config={"model": "gpt-4o", "temperature": 0.1}
        )
        
        style_reviewer = AssistantAgent(
            name="style_reviewer",
            system_message=f"""You are a code quality expert. Review this {language} code for:
            - Code readability and maintainability
            - Naming conventions
            - Code structure and organization
            - Documentation quality
            Provide style improvement suggestions.""",
            llm_config={"model": "gpt-4o", "temperature": 0.1}
        )

        # Execute review workflow
        result = {
            "workflow": "code_review",
            "language": language,
            "focus_areas": focus_areas,
            "timestamp": datetime.now().isoformat(),
            "reviews": []
        }

        # Conduct reviews
        for reviewer in [security_reviewer, performance_reviewer, style_reviewer]:
            review_result = reviewer.initiate_chat(
                security_reviewer if reviewer != security_reviewer else performance_reviewer,
                message=f"Review this {language} code:\n\n{code}",
                max_turns=2
            )
            result["reviews"].append({
                "reviewer": reviewer.name,
                "result": str(review_result)
            })

        return result

    async def _execute_custom_workflow(
        self, workflow_config: Dict[str, Any], input_data: Dict[str, Any], 
        output_format: str, quality_checks: bool
    ) -> Dict[str, Any]:
        """Execute a custom workflow based on configuration."""
        # Simplified implementation for custom workflows
        return {
            "workflow": workflow_config.get("name", "custom"),
            "type": workflow_config.get("type", "unknown"),
            "agents": workflow_config.get("agents", []),
            "input": input_data,
            "result": "Custom workflow executed",
            "format": output_format,
            "timestamp": datetime.now().isoformat()
        }

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
                agent.reset_consecutive_auto_reply_counter()        return chat_history
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
