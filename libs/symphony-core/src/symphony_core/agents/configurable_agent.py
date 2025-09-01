"""
Configurable Agent - Hybrid Configuration + Python Architecture
Supports both configuration-driven and Python code-driven agent definitions
"""

import asyncio
import yaml
import re
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentCapability, create_agent_capability, AgentSchedule
from .base_agent import HandoffContext, HandoffStatus


@dataclass
class ConfigCommand:
    """Represents a configuration-driven command"""
    name: str
    description: str
    task: Optional[str] = None
    template: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class AgentConfig:
    """Parsed agent configuration from markdown + YAML"""
    name: str
    agent_id: str
    title: str
    icon: str
    when_to_use: str
    role: str
    identity: str
    style: Optional[str] = None
    focus: Optional[str] = None
    core_principles: List[str] = None
    commands: List[ConfigCommand] = None
    dependencies: Dict[str, List[str]] = None
    customization: Optional[Dict[str, Any]] = None


class ConfigurableAgent(BaseAgent):
    """
    Hybrid Agent supporting both configuration-driven and Python code-driven approaches
    
    Features:
    - Load agent behavior from Markdown + YAML definitions
    - Execute configuration-style commands (*help, *create, *task)
    - Use YAML templates for standardized outputs
    - Maintain Python performance and enterprise integration
    - Support runtime configuration changes
    """
    
    def __init__(self, config_source: Union[str, Dict[str, Any], AgentConfig], 
                 customer_id: Optional[str] = None):
        
        self.agent_config: Optional[AgentConfig] = None
        self.config_commands: Dict[str, ConfigCommand] = {}
        self.template_cache: Dict[str, Dict[str, Any]] = {}
        self.task_cache: Dict[str, str] = {}
        
        # Load configuration based on source type
        if isinstance(config_source, str):
            # Load from markdown file
            self.agent_config = self._load_config_file(config_source)
        elif isinstance(config_source, AgentConfig):
            # Direct config object
            self.agent_config = config_source
        elif isinstance(config_source, dict):
            # Dictionary configuration (Python style)
            self.agent_config = self._convert_dict_to_config(config_source)
        else:
            raise ValueError(f"Unsupported config source type: {type(config_source)}")
        
        # Convert config to BaseAgent parameters
        capabilities = self._create_capabilities_from_config()
        schedule = self._create_schedule_from_config()
        
        # Initialize BaseAgent
        super().__init__(
            agent_id=self.agent_config.agent_id,
            name=self.agent_config.name,
            role=self.agent_config.role,
            category=self._determine_category(),
            capabilities=capabilities,
            schedule=schedule,
            customer_id=customer_id
        )
        
        # Build command index for efficient lookup
        if self.agent_config.commands:
            for cmd in self.agent_config.commands:
                self.config_commands[cmd.name] = cmd
                # Support both *command and command formats
                self.config_commands[f"*{cmd.name}"] = cmd
        
    def _load_config_file(self, file_path: str) -> AgentConfig:
        """Load and parse agent definition from markdown file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Agent config file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self._parse_config_content(content)
    
    def _parse_config_content(self, content: str) -> AgentConfig:
        """Parse agent definition from markdown content"""
        # Extract YAML block from markdown
        yaml_match = re.search(r'```yaml\n(.*?)\n```', content, re.DOTALL)
        if not yaml_match:
            raise ValueError("No YAML configuration block found in agent config file")
        
        yaml_content = yaml_match.group(1)
        
        try:
            config_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in agent config file: {e}")
        
        # Parse agent section
        agent_section = config_data.get('agent', {})
        persona_section = config_data.get('persona', {})
        commands_section = config_data.get('commands', [])
        dependencies_section = config_data.get('dependencies', {})
        
        # Parse commands
        config_commands = []
        for cmd_def in commands_section:
            if isinstance(cmd_def, str):
                # Simple command: "help: Show help"
                if ':' in cmd_def:
                    name, desc = cmd_def.split(':', 1)
                    config_commands.append(ConfigCommand(name.strip(), desc.strip()))
                else:
                    config_commands.append(ConfigCommand(cmd_def.strip(), f"Execute {cmd_def}"))
            elif isinstance(cmd_def, dict):
                # Complex command with parameters
                for name, details in cmd_def.items():
                    if isinstance(details, str):
                        config_commands.append(ConfigCommand(name, details))
                    elif isinstance(details, dict):
                        config_commands.append(ConfigCommand(
                            name=name,
                            description=details.get('description', f'Execute {name}'),
                            task=details.get('task'),
                            template=details.get('template'),
                            parameters=details.get('parameters', {})
                        ))
        
        # Create config object
        return AgentConfig(
            name=agent_section.get('name', 'Unknown Agent'),
            agent_id=agent_section.get('id', 'unknown-agent'),
            title=agent_section.get('title', 'Unknown Title'),
            icon=agent_section.get('icon', '🤖'),
            when_to_use=agent_section.get('whenToUse', 'General purpose agent'),
            role=persona_section.get('role', 'General Agent'),
            identity=persona_section.get('identity', 'AI Assistant'),
            style=persona_section.get('style'),
            focus=persona_section.get('focus'),
            core_principles=persona_section.get('core_principles', []),
            commands=config_commands,
            dependencies=dependencies_section
        )
    
    def _convert_dict_to_config(self, config_dict: Dict[str, Any]) -> AgentConfig:
        """Convert dictionary configuration to config format"""
        return AgentConfig(
            name=config_dict.get('name', 'Unknown Agent'),
            agent_id=config_dict.get('agent_id', 'unknown-agent'),
            title=config_dict.get('title', 'Unknown Title'),
            icon=config_dict.get('icon', '🤖'),
            when_to_use=config_dict.get('when_to_use', 'General purpose agent'),
            role=config_dict.get('role', 'General Agent'),
            identity=config_dict.get('identity', 'AI Assistant'),
            style=config_dict.get('style'),
            focus=config_dict.get('focus'),
            core_principles=config_dict.get('core_principles', []),
            commands=[],  # Would need to be converted from dict format
            dependencies=config_dict.get('dependencies', {})
        )
    
    def _create_capabilities_from_config(self) -> List[AgentCapability]:
        """Create agent capabilities from configuration"""
        capabilities = []
        
        # Core capability based on role
        capabilities.append(
            create_agent_capability(
                "config_command_execution",
                f"Execute configuration-driven commands for {self.agent_config.role}",
                "critical"
            )
        )
        
        # Add capabilities based on available commands
        if self.agent_config.commands:
            for cmd in self.agent_config.commands:
                if cmd.name in ['help', 'exit']:
                    continue  # Skip basic commands
                
                capabilities.append(
                    create_agent_capability(
                        f"command_{cmd.name}",
                        cmd.description,
                        "high" if cmd.task else "medium"
                    )
                )
        
        # Add template-based capabilities
        if self.agent_config.dependencies and 'templates' in self.agent_config.dependencies:
            capabilities.append(
                create_agent_capability(
                    "template_processing",
                    "Process and generate content from YAML templates",
                    "high"
                )
            )
        
        # Add task execution capability
        if self.agent_config.dependencies and 'tasks' in self.agent_config.dependencies:
            capabilities.append(
                create_agent_capability(
                    "task_orchestration",
                    "Execute complex tasks and workflows",
                    "high"
                )
            )
        
        return capabilities
    
    def _create_schedule_from_config(self) -> AgentSchedule:
        """Create agent schedule from configuration"""
        # Default schedule for config-driven agents (typically interactive)
        return AgentSchedule(
            morning_start="8:00 AM EST",
            midday_optimization="12:00 PM EST", 
            evening_planning="5:00 PM EST",
            timezone="EST",
            enabled=True
        )
    
    def _determine_category(self) -> str:
        """Determine agent category from configuration"""
        role_lower = self.agent_config.role.lower()
        
        if any(term in role_lower for term in ['master', 'orchestrator', 'coordinator']):
            return 'coordinators'
        elif any(term in role_lower for term in ['manager', 'lead', 'director']):
            return 'managers'
        elif any(term in role_lower for term in ['architect', 'strategist', 'analyst']):
            return 'leads'
        else:
            return 'specialists'
    
    async def _initialize_agent(self) -> None:
        """Initialize configurable agent with configuration context"""
        await super()._initialize_agent()
        
        # Load dependencies if specified
        await self._load_dependencies()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Configurable Agent {self.name} ({self.agent_config.icon}) initialized with "
            f"{len(self.config_commands)} commands and configuration compatibility"
        )
    
    async def _load_dependencies(self):
        """Load configuration dependencies (templates, tasks, checklists, data)"""
        if not self.agent_config.dependencies:
            return
        
        # Load templates
        templates = self.agent_config.dependencies.get('templates', [])
        for template_name in templates:
            await self._load_template(template_name)
        
        # Load tasks
        tasks = self.agent_config.dependencies.get('tasks', [])
        for task_name in tasks:
            await self._load_task(task_name)
    
    async def _load_template(self, template_name: str):
        """Load YAML template for standardized outputs"""
        try:
            # Import template engine
            from ..templates.template_engine import TemplateEngine
            
            # Initialize template engine if not already done
            if not hasattr(self, '_template_engine'):
                self._template_engine = TemplateEngine()
            
            # Load template through engine
            template_data = self._template_engine.load_template(template_name)
            self.template_cache[template_name] = template_data
            
        except Exception as e:
            # Fallback to placeholder if template loading fails
            self.template_cache[template_name] = {
                "template_info": {
                    "name": template_name,
                    "version": "1.0",
                    "description": f"Placeholder template for {template_name}",
                    "category": "placeholder"
                },
                "sections": {
                    "header": "# Generated by {agent_name}",
                    "content": f"Content generated from template: {template_name}",
                    "footer": "Generated at: {timestamp}"
                },
                "default_values": {},
                "error": str(e)
            }
    
    async def _load_task(self, task_name: str):
        """Load task definition for execution"""
        # In a full implementation, this would load from the task directory
        # For now, we'll create a placeholder
        self.task_cache[task_name] = f"Task: {task_name} - Execute {task_name} workflow"
    
    async def _execute_task_impl(self, task_data: Dict[str, Any]) -> Any:
        """Execute configurable agent tasks"""
        task_type = task_data.get("type", "unknown")
        
        # Check if this is a config command
        if task_type.startswith("config_command:"):
            command_name = task_type.split(":", 1)[1]
            return await self._execute_config_command(command_name, task_data)
        
        # Handle standard task types
        if task_type == "config_help":
            return await self._execute_help_command()
        elif task_type == "template_generation":
            return await self._execute_template_generation(task_data)
        elif task_type == "task_execution":
            return await self._execute_task_workflow(task_data)
        else:
            # Fallback to base agent task execution
            return await super()._execute_task_impl(task_data)
    
    async def _execute_config_command(self, command_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute configuration-driven command"""
        # Remove * prefix if present
        if command_name.startswith('*'):
            command_name = command_name[1:]
        
        command = self.config_commands.get(command_name)
        if not command:
            return {
                "success": False,
                "error": f"Unknown command: {command_name}",
                "available_commands": list(self.config_commands.keys())
            }
        
        # Execute based on command type
        if command.name == "help":
            return await self._execute_help_command()
        elif command.task:
            return await self._execute_task_workflow({
                "task_name": command.task,
                "parameters": command.parameters or {},
                **context
            })
        elif command.template:
            return await self._execute_template_generation({
                "template_name": command.template,
                "parameters": command.parameters or {},
                **context
            })
        else:
            # Generic command execution
            return {
                "success": True,
                "command": command.name,
                "description": command.description,
                "executed_at": datetime.now().isoformat(),
                "result": f"Executed {command.name}: {command.description}"
            }
    
    async def _execute_help_command(self) -> Dict[str, Any]:
        """Execute configuration help command"""
        help_info = {
            "agent_name": self.agent_config.name,
            "agent_icon": self.agent_config.icon,
            "agent_title": self.agent_config.title,
            "when_to_use": self.agent_config.when_to_use,
            "role": self.agent_config.role,
            "identity": self.agent_config.identity,
            "available_commands": []
        }
        
        # Add commands with descriptions
        for cmd_name, cmd in self.config_commands.items():
            if not cmd_name.startswith('*'):  # Avoid duplicates
                help_info["available_commands"].append({
                    "command": f"*{cmd_name}",
                    "description": cmd.description
                })
        
        # Add core principles if available
        if self.agent_config.core_principles:
            help_info["core_principles"] = self.agent_config.core_principles
        
        return {
            "success": True,
            "help_info": help_info,
            "config_compatible": True
        }
    
    async def _execute_template_generation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute template-based content generation"""
        template_name = context.get("template_name")
        parameters = context.get("parameters", {})
        
        if not template_name or template_name not in self.template_cache:
            return {
                "success": False,
                "error": f"Template not found: {template_name}",
                "available_templates": list(self.template_cache.keys())
            }
        
        template = self.template_cache[template_name]
        
        # Check if this is a full template with template engine support
        if "template_info" in template and hasattr(self, '_template_engine'):
            # Use template engine for full document generation
            try:
                result = self._template_engine.generate_document(
                    template_name, 
                    parameters,
                    agent_name=self.name
                )
                
                if result['success']:
                    return {
                        "success": True,
                        "template_name": template_name,
                        "generated_document": result['document'],
                        "generated_sections": result['sections'],
                        "template_info": result['template_info'],
                        "parameters_used": result['parameters_used'],
                        "generated_at": result['generated_at'],
                        "engine_generated": True
                    }
                else:
                    return {
                        "success": False,
                        "error": "Template generation failed",
                        "validation_errors": result.get('errors', []),
                        "template_name": template_name
                    }
            except Exception as e:
                # Fall back to simple generation
                pass
        
        # Fallback to simple template generation
        generated_content = {}
        for section_name, section_template in template.get("sections", {}).items():
            try:
                generated_content[section_name] = section_template.format(
                    agent_name=self.name,
                    template_name=template_name,
                    timestamp=datetime.now().isoformat(),
                    **parameters
                )
            except KeyError as e:
                param_name = str(e).strip("'")
                generated_content[section_name] = f"[Missing parameter: {param_name}]"
        
        return {
            "success": True,
            "template_name": template_name,
            "generated_content": generated_content,
            "parameters_used": parameters,
            "engine_generated": False
        }
    
    async def _execute_task_workflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute configuration task workflow"""
        task_name = context.get("task_name")
        parameters = context.get("parameters", {})
        
        if not task_name or task_name not in self.task_cache:
            return {
                "success": False,
                "error": f"Task not found: {task_name}",
                "available_tasks": list(self.task_cache.keys())
            }
        
        task_definition = self.task_cache[task_name]
        
        # Execute task workflow (simplified for demonstration)
        result = {
            "success": True,
            "task_name": task_name,
            "task_definition": task_definition,
            "parameters": parameters,
            "execution_time": datetime.now().isoformat(),
            "workflow_steps": [
                {"step": 1, "description": f"Initialize {task_name}", "status": "completed"},
                {"step": 2, "description": f"Process {task_name}", "status": "completed"},
                {"step": 3, "description": f"Finalize {task_name}", "status": "completed"}
            ]
        }
        
        return result
    
    async def _process_handoff(self, handoff_context: HandoffContext) -> bool:
        """Process handoff with configuration context awareness"""
        try:
            # Check if handoff includes config command
            config_command = handoff_context.context_data.get("config_command")
            if config_command:
                # Execute config command as part of handoff
                command_result = await self._execute_config_command(config_command, handoff_context.context_data)
                handoff_context.context_data["config_command_result"] = command_result
            
            # Add config agent context
            handoff_context.context_data.update({
                "config_agent_config": {
                    "name": self.agent_config.name,
                    "role": self.agent_config.role,
                    "identity": self.agent_config.identity,
                    "capabilities": list(self.config_commands.keys())
                }
            })
            
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing config handoff {handoff_context.handoff_id}: {str(e)}")
            return False
    
    def get_agent_config(self) -> AgentConfig:
        """Get the configuration for this agent"""
        return self.agent_config
    
    def get_available_commands(self) -> Dict[str, str]:
        """Get available configuration commands with descriptions"""
        return {name: cmd.description for name, cmd in self.config_commands.items() if not name.startswith('*')}
    
    def supports_command(self, command_name: str) -> bool:
        """Check if agent supports a specific configuration command"""
        return command_name in self.config_commands or f"*{command_name}" in self.config_commands