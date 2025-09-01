"""
Agent Factory for Symphony Hybrid Architecture
Supports both configuration-driven and Python code-driven agent creation
"""

import os
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Type
from dataclasses import dataclass
from enum import Enum

from ..agents.base_agent import BaseAgent
from ..agents.configurable_agent import ConfigurableAgent, AgentConfig


logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents supported by the factory"""
    CONFIG_DRIVEN = "config_driven"      # Markdown + YAML configuration
    PYTHON_DRIVEN = "python_driven"      # Pure Python implementation
    HYBRID = "hybrid"                    # Both config and Python capabilities


@dataclass
class AgentRegistration:
    """Registration information for an agent type"""
    agent_id: str
    agent_type: AgentType
    source: str                          # File path or class reference
    name: str
    description: str
    category: str
    priority: int = 50                   # Lower numbers = higher priority
    enabled: bool = True


class AgentFactory:
    """
    Factory for creating Symphony agents with hybrid architecture support
    
    Features:
    - Create configuration-driven agents from markdown files
    - Create Python-driven agents from classes
    - Auto-discovery of agents in directories
    - Agent registration and management
    - Validation and error handling
    - Performance optimization through caching
    """
    
    def __init__(self, 
                 config_agent_dir: Optional[str] = None,
                 python_agent_dir: Optional[str] = None,
                 template_dir: Optional[str] = None):
        """
        Initialize agent factory
        
        Args:
            config_agent_dir: Directory containing markdown agent configs
            python_agent_dir: Directory containing Python agent classes
            template_dir: Directory containing YAML templates
        """
        self.config_agent_dir = config_agent_dir
        self.python_agent_dir = python_agent_dir
        self.template_dir = template_dir
        
        # Registry of available agents
        self.registered_agents: Dict[str, AgentRegistration] = {}
        
        # Cache for loaded agent classes and configs
        self.agent_class_cache: Dict[str, Type[BaseAgent]] = {}
        self.config_cache: Dict[str, AgentConfig] = {}
        
        # Auto-discovery on initialization
        self.discover_agents()
    
    def discover_agents(self):
        """Auto-discover agents from configured directories"""
        logger.info("Starting agent discovery...")
        
        discovered_count = 0
        
        # Discover configuration-driven agents
        if self.config_agent_dir and os.path.exists(self.config_agent_dir):
            discovered_count += self._discover_config_agents()
        
        # Discover Python-driven agents  
        if self.python_agent_dir and os.path.exists(self.python_agent_dir):
            discovered_count += self._discover_python_agents()
        
        logger.info(f"Agent discovery completed. Found {discovered_count} agents.")
    
    def _discover_config_agents(self) -> int:
        """Discover configuration-driven agents from markdown files"""
        config_dir = Path(self.config_agent_dir)
        discovered = 0
        
        for md_file in config_dir.glob("*.md"):
            try:
                # Load agent config to get metadata
                agent_config = self._load_agent_config(str(md_file))
                
                # Register the agent
                self.register_agent(
                    agent_id=agent_config.agent_id,
                    agent_type=AgentType.CONFIG_DRIVEN,
                    source=str(md_file),
                    name=agent_config.name,
                    description=f"{agent_config.title}: {agent_config.when_to_use}",
                    category=self._determine_category_from_role(agent_config.role)
                )
                
                discovered += 1
                logger.debug(f"Discovered config agent: {agent_config.name} ({agent_config.agent_id})")
                
            except Exception as e:
                logger.warning(f"Failed to load config agent from {md_file}: {e}")
        
        return discovered
    
    def _discover_python_agents(self) -> int:
        """Discover Python-driven agents from class files"""
        python_dir = Path(self.python_agent_dir)
        discovered = 0
        
        # Look for Python files containing agent classes
        for py_file in python_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue  # Skip __init__.py, __pycache__, etc.
            
            try:
                # Import module and find BaseAgent subclasses
                module_name = py_file.stem
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find agent classes in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseAgent) and 
                        attr != BaseAgent and
                        attr != ConfigurableAgent):
                        
                        # Register the Python agent
                        agent_id = getattr(attr, 'AGENT_ID', None) or f"{module_name}_{attr_name.lower()}"
                        
                        self.register_agent(
                            agent_id=agent_id,
                            agent_type=AgentType.PYTHON_DRIVEN,
                            source=f"{module_name}.{attr_name}",
                            name=getattr(attr, 'AGENT_NAME', attr_name),
                            description=getattr(attr, 'AGENT_DESCRIPTION', f"Python agent: {attr_name}"),
                            category=getattr(attr, 'AGENT_CATEGORY', 'specialists')
                        )
                        
                        # Cache the class
                        self.agent_class_cache[agent_id] = attr
                        
                        discovered += 1
                        logger.debug(f"Discovered Python agent: {attr_name} ({agent_id})")
                        
            except Exception as e:
                logger.warning(f"Failed to load Python agent from {py_file}: {e}")
        
        return discovered
    
    def register_agent(self,
                      agent_id: str,
                      agent_type: AgentType,
                      source: str,
                      name: str,
                      description: str,
                      category: str,
                      priority: int = 50,
                      enabled: bool = True):
        """Register an agent with the factory"""
        registration = AgentRegistration(
            agent_id=agent_id,
            agent_type=agent_type,
            source=source,
            name=name,
            description=description,
            category=category,
            priority=priority,
            enabled=enabled
        )
        
        self.registered_agents[agent_id] = registration
        logger.debug(f"Registered agent: {name} ({agent_id}) - {agent_type.value}")
    
    def create_agent(self, 
                    agent_id: str, 
                    customer_id: Optional[str] = None,
                    override_config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        """
        Create an agent instance by ID
        
        Args:
            agent_id: ID of the agent to create
            customer_id: Customer ID for the agent instance
            override_config: Optional configuration overrides
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent ID is not registered
            Exception: If agent creation fails
        """
        if agent_id not in self.registered_agents:
            available_agents = list(self.registered_agents.keys())
            raise ValueError(f"Agent '{agent_id}' not registered. Available: {available_agents}")
        
        registration = self.registered_agents[agent_id]
        
        if not registration.enabled:
            raise ValueError(f"Agent '{agent_id}' is disabled")
        
        try:
            if registration.agent_type == AgentType.CONFIG_DRIVEN:
                return self._create_config_agent(registration, customer_id, override_config)
            elif registration.agent_type == AgentType.PYTHON_DRIVEN:
                return self._create_python_agent(registration, customer_id, override_config)
            elif registration.agent_type == AgentType.HYBRID:
                return self._create_hybrid_agent(registration, customer_id, override_config)
            else:
                raise ValueError(f"Unsupported agent type: {registration.agent_type}")
                
        except Exception as e:
            logger.error(f"Failed to create agent '{agent_id}': {e}")
            raise
    
    def _create_config_agent(self, 
                           registration: AgentRegistration,
                           customer_id: Optional[str],
                           override_config: Optional[Dict[str, Any]]) -> ConfigurableAgent:
        """Create a configuration-driven agent"""
        # Load agent config if not cached
        if registration.agent_id not in self.config_cache:
            agent_config = self._load_agent_config(registration.source)
            self.config_cache[registration.agent_id] = agent_config
        else:
            agent_config = self.config_cache[registration.agent_id]
        
        # Apply configuration overrides
        if override_config:
            # Convert to dict, apply overrides, convert back
            config_dict = self._agent_config_to_dict(agent_config)
            config_dict.update(override_config)
            agent_config = self._dict_to_agent_config(config_dict)
        
        # Create the configurable agent
        return ConfigurableAgent(agent_config, customer_id=customer_id)
    
    def _create_python_agent(self,
                           registration: AgentRegistration,
                           customer_id: Optional[str], 
                           override_config: Optional[Dict[str, Any]]) -> BaseAgent:
        """Create a Python-driven agent"""
        # Get the agent class
        if registration.agent_id not in self.agent_class_cache:
            # Load the class dynamically
            module_name, class_name = registration.source.rsplit('.', 1)
            module = importlib.import_module(module_name)
            agent_class = getattr(module, class_name)
            self.agent_class_cache[registration.agent_id] = agent_class
        else:
            agent_class = self.agent_class_cache[registration.agent_id]
        
        # Create instance with customer ID
        # Note: This assumes the Python agent constructor accepts customer_id
        try:
            return agent_class(customer_id=customer_id, **(override_config or {}))
        except TypeError:
            # Fallback for agents that don't accept customer_id parameter
            return agent_class(**(override_config or {}))
    
    def _create_hybrid_agent(self,
                           registration: AgentRegistration,
                           customer_id: Optional[str],
                           override_config: Optional[Dict[str, Any]]) -> BaseAgent:
        """Create a hybrid agent (future implementation)"""
        # For now, treat as config agent
        return self._create_config_agent(registration, customer_id, override_config)
    
    def _load_agent_config(self, config_path: str) -> AgentConfig:
        """Load agent configuration from markdown file"""
        config_agent = ConfigurableAgent(config_path)
        return config_agent.get_agent_config()
    
    def _agent_config_to_dict(self, config: AgentConfig) -> Dict[str, Any]:
        """Convert AgentConfig to dictionary"""
        return {
            'name': config.name,
            'agent_id': config.agent_id,
            'title': config.title,
            'icon': config.icon,
            'when_to_use': config.when_to_use,
            'role': config.role,
            'identity': config.identity,
            'style': config.style,
            'focus': config.focus,
            'core_principles': config.core_principles,
            'dependencies': config.dependencies
        }
    
    def _dict_to_agent_config(self, config_dict: Dict[str, Any]) -> AgentConfig:
        """Convert dictionary to AgentConfig"""
        return AgentConfig(
            name=config_dict['name'],
            agent_id=config_dict['agent_id'],
            title=config_dict['title'],
            icon=config_dict['icon'],
            when_to_use=config_dict['when_to_use'],
            role=config_dict['role'],
            identity=config_dict['identity'],
            style=config_dict.get('style'),
            focus=config_dict.get('focus'),
            core_principles=config_dict.get('core_principles', []),
            commands=None,  # Would need separate conversion
            dependencies=config_dict.get('dependencies', {})
        )
    
    def _determine_category_from_role(self, role: str) -> str:
        """Determine agent category from role string"""
        role_lower = role.lower()
        
        if any(term in role_lower for term in ['master', 'orchestrator', 'coordinator']):
            return 'coordinators'
        elif any(term in role_lower for term in ['manager', 'lead', 'director']):
            return 'managers'
        elif any(term in role_lower for term in ['architect', 'strategist', 'analyst']):
            return 'leads'
        else:
            return 'specialists'
    
    def list_agents(self, 
                   category: Optional[str] = None,
                   agent_type: Optional[AgentType] = None,
                   enabled_only: bool = True) -> List[AgentRegistration]:
        """
        List registered agents with optional filtering
        
        Args:
            category: Filter by agent category
            agent_type: Filter by agent type
            enabled_only: Only return enabled agents
            
        Returns:
            List of agent registrations
        """
        agents = list(self.registered_agents.values())
        
        # Apply filters
        if enabled_only:
            agents = [a for a in agents if a.enabled]
        
        if category:
            agents = [a for a in agents if a.category == category]
        
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        
        # Sort by priority (lower numbers first), then by name
        agents.sort(key=lambda a: (a.priority, a.name))
        
        return agents
    
    def get_agent_info(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get registration information for an agent"""
        return self.registered_agents.get(agent_id)
    
    def enable_agent(self, agent_id: str):
        """Enable an agent"""
        if agent_id in self.registered_agents:
            self.registered_agents[agent_id].enabled = True
            logger.info(f"Enabled agent: {agent_id}")
    
    def disable_agent(self, agent_id: str):
        """Disable an agent"""
        if agent_id in self.registered_agents:
            self.registered_agents[agent_id].enabled = False
            logger.info(f"Disabled agent: {agent_id}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get factory statistics"""
        total_agents = len(self.registered_agents)
        enabled_agents = len([a for a in self.registered_agents.values() if a.enabled])
        
        by_type = {}
        by_category = {}
        
        for agent in self.registered_agents.values():
            # Count by type
            type_key = agent.agent_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            # Count by category
            by_category[agent.category] = by_category.get(agent.category, 0) + 1
        
        return {
            'total_agents': total_agents,
            'enabled_agents': enabled_agents,
            'disabled_agents': total_agents - enabled_agents,
            'by_type': by_type,
            'by_category': by_category,
            'cache_stats': {
                'config_cache_size': len(self.config_cache),
                'class_cache_size': len(self.agent_class_cache)
            }
        }


# Factory instance and convenience functions
_default_factory: Optional[AgentFactory] = None


def get_default_factory() -> AgentFactory:
    """Get the default agent factory instance"""
    global _default_factory
    if _default_factory is None:
        # Initialize with default directories
        current_dir = Path(__file__).parent.parent
        _default_factory = AgentFactory(
            config_agent_dir=str(current_dir / "agents"),
            python_agent_dir=str(current_dir / "agents"),
            template_dir=str(current_dir / "templates")
        )
    return _default_factory


def create_agent(agent_id: str, customer_id: Optional[str] = None) -> BaseAgent:
    """Convenience function to create an agent using the default factory"""
    return get_default_factory().create_agent(agent_id, customer_id)


def list_available_agents(category: Optional[str] = None) -> List[AgentRegistration]:
    """Convenience function to list available agents"""
    return get_default_factory().list_agents(category=category)


def register_agent_class(agent_class: Type[BaseAgent], 
                        agent_id: Optional[str] = None,
                        priority: int = 50):
    """Convenience function to register a Python agent class"""
    factory = get_default_factory()
    
    agent_id = agent_id or getattr(agent_class, 'AGENT_ID', agent_class.__name__.lower())
    
    factory.register_agent(
        agent_id=agent_id,
        agent_type=AgentType.PYTHON_DRIVEN,
        source=f"{agent_class.__module__}.{agent_class.__name__}",
        name=getattr(agent_class, 'AGENT_NAME', agent_class.__name__),
        description=getattr(agent_class, 'AGENT_DESCRIPTION', f"Python agent: {agent_class.__name__}"),
        category=getattr(agent_class, 'AGENT_CATEGORY', 'specialists'),
        priority=priority
    )
    
    # Cache the class
    factory.agent_class_cache[agent_id] = agent_class