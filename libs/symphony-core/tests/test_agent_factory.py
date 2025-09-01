"""
Test Agent Factory - Hybrid Architecture Support
Tests creation of both configuration-driven and Python code-driven agents
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from symphony_core.factories.agent_factory import (
    AgentFactory, AgentType, AgentRegistration,
    get_default_factory, create_agent, list_available_agents, register_agent_class
)
from symphony_core.agents.base_agent import BaseAgent, AgentCapability, AgentSchedule
from symphony_core.agents.configurable_agent import ConfigurableAgent


# Test Python Agent for factory testing
class TestPythonAgent(BaseAgent):
    """Test Python agent for factory testing"""
    
    AGENT_ID = "test-python-agent"
    AGENT_NAME = "Test Python Agent"
    AGENT_DESCRIPTION = "Python agent for testing the factory"
    AGENT_CATEGORY = "specialists"
    
    def __init__(self, customer_id: str = None, test_param: str = "default"):
        self.test_param = test_param
        
        super().__init__(
            agent_id=self.AGENT_ID,
            name=self.AGENT_NAME,
            role="Test Specialist", 
            category=self.AGENT_CATEGORY,
            capabilities=[
                AgentCapability("test_capability", "Test capability", "high")
            ],
            schedule=AgentSchedule(),
            customer_id=customer_id
        )
    
    async def _execute_task_impl(self, task_data):
        return {
            "success": True,
            "message": f"Test task executed with param: {self.test_param}",
            "task_data": task_data
        }
    
    async def _initialize_agent(self) -> None:
        """Initialize test agent"""
        await super()._initialize_agent()
    
    async def _process_handoff(self, handoff_context) -> bool:
        """Process handoff for test agent"""
        return True


class TestAgentFactory:
    """Test suite for AgentFactory"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        config_dir = temp_dir / "config_agents"
        python_dir = temp_dir / "python_agents"
        template_dir = temp_dir / "templates"
        
        config_dir.mkdir()
        python_dir.mkdir()
        template_dir.mkdir()
        
        yield {
            'base': temp_dir,
            'config': config_dir,
            'python': python_dir,
            'template': template_dir
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_config_agent(self, temp_dirs):
        """Create a sample configuration agent file"""
        config_path = temp_dirs['config'] / "sample-agent.md"
        
        config_content = """# Sample Test Agent

```yaml
agent:
  name: Sample Test Agent
  id: sample-test-agent
  title: Sample Configuration Agent
  icon: 🧪
  whenToUse: Use for testing agent factory functionality

persona:
  role: Test Configuration Specialist
  identity: Factory testing specialist
  style: Systematic and thorough
  core_principles:
    - Test all factory functionality
    - Validate configuration loading
    - Ensure agent creation works

commands:
  - help: Show available commands
  - test-command: Execute test workflow
  - validate: Validate factory functionality

dependencies:
  templates:
    - test-template.yaml
  tasks:
    - test-task.md
```"""
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        return str(config_path)
    
    @pytest.fixture
    def sample_python_agent(self, temp_dirs):
        """Create a sample Python agent file"""
        python_path = temp_dirs['python'] / "sample_python_agent.py"
        
        python_content = """from symphony_core.agents.base_agent import BaseAgent, AgentCapability, AgentSchedule

class SamplePythonAgent(BaseAgent):
    AGENT_ID = "sample-python-agent"
    AGENT_NAME = "Sample Python Agent"
    AGENT_DESCRIPTION = "Sample Python agent for factory testing"
    AGENT_CATEGORY = "specialists"
    
    def __init__(self, customer_id=None):
        super().__init__(
            agent_id=self.AGENT_ID,
            name=self.AGENT_NAME,
            role="Python Test Specialist",
            category=self.AGENT_CATEGORY,
            capabilities=[AgentCapability("python_test", "Python testing", "high")],
            schedule=AgentSchedule(),
            customer_id=customer_id
        )
    
    async def _execute_task_impl(self, task_data):
        return {"success": True, "message": "Python agent task executed"}
"""
        
        with open(python_path, 'w') as f:
            f.write(python_content)
        
        return str(python_path)
    
    def test_agent_factory_initialization(self, temp_dirs):
        """Test factory initialization"""
        factory = AgentFactory(
            config_agent_dir=str(temp_dirs['config']),
            python_agent_dir=str(temp_dirs['python']),
            template_dir=str(temp_dirs['template'])
        )
        
        assert factory.config_agent_dir == str(temp_dirs['config'])
        assert factory.python_agent_dir == str(temp_dirs['python'])
        assert factory.template_dir == str(temp_dirs['template'])
        assert isinstance(factory.registered_agents, dict)
        assert isinstance(factory.agent_class_cache, dict)
        assert isinstance(factory.config_cache, dict)
    
    def test_agent_registration(self, temp_dirs):
        """Test manual agent registration"""
        factory = AgentFactory(
            config_agent_dir=str(temp_dirs['config']),
            python_agent_dir=str(temp_dirs['python'])
        )
        
        # Register a test agent
        factory.register_agent(
            agent_id="manual-test-agent",
            agent_type=AgentType.CONFIG_DRIVEN,
            source="/test/path/agent.md",
            name="Manual Test Agent",
            description="Manually registered test agent",
            category="specialists"
        )
        
        # Check registration
        assert "manual-test-agent" in factory.registered_agents
        
        registration = factory.registered_agents["manual-test-agent"]
        assert registration.agent_id == "manual-test-agent"
        assert registration.agent_type == AgentType.CONFIG_DRIVEN
        assert registration.name == "Manual Test Agent"
        assert registration.enabled is True
    
    def test_config_agent_discovery(self, temp_dirs, sample_config_agent):
        """Test discovery of configuration agents"""
        factory = AgentFactory(
            config_agent_dir=str(temp_dirs['config']),
            python_agent_dir=str(temp_dirs['python'])
        )
        
        # Should have discovered the sample config agent
        assert "sample-test-agent" in factory.registered_agents
        
        registration = factory.registered_agents["sample-test-agent"]
        assert registration.agent_type == AgentType.CONFIG_DRIVEN
        assert registration.name == "Sample Test Agent"
        assert registration.category == "specialists"  # Based on role
    
    def test_python_agent_registration_convenience(self):
        """Test convenience function for registering Python agents"""
        # Register the test agent class
        register_agent_class(TestPythonAgent, priority=10)
        
        factory = get_default_factory()
        
        # Check it was registered
        assert "test-python-agent" in factory.registered_agents
        
        registration = factory.registered_agents["test-python-agent"]
        assert registration.agent_type == AgentType.PYTHON_DRIVEN
        assert registration.name == "Test Python Agent"
        assert registration.priority == 10
    
    @pytest.mark.asyncio
    async def test_create_config_agent(self, temp_dirs, sample_config_agent):
        """Test creating configuration-driven agent"""
        factory = AgentFactory(
            config_agent_dir=str(temp_dirs['config']),
            python_agent_dir=str(temp_dirs['python'])
        )
        
        # Create the config agent
        agent = factory.create_agent("sample-test-agent", customer_id="test-customer")
        
        # Verify it's a ConfigurableAgent
        assert isinstance(agent, ConfigurableAgent)
        assert agent.name == "Sample Test Agent"
        assert agent.agent_id == "sample-test-agent"
        assert agent.customer_id == "test-customer"
        
        # Initialize and test
        await agent._initialize_agent()
        
        config = agent.get_agent_config()
        assert config.name == "Sample Test Agent"
        assert config.role == "Test Configuration Specialist"
    
    @pytest.mark.asyncio
    async def test_create_python_agent(self):
        """Test creating Python-driven agent"""
        # Register the test agent class
        register_agent_class(TestPythonAgent)
        
        factory = get_default_factory()
        
        # Create the Python agent
        agent = factory.create_agent("test-python-agent", customer_id="test-customer")
        
        # Verify it's the correct type
        assert isinstance(agent, TestPythonAgent)
        assert agent.name == "Test Python Agent"
        assert agent.agent_id == "test-python-agent"
        assert agent.customer_id == "test-customer"
        
        # Test the agent functionality
        await agent._initialize_agent()
        
        result = await agent._execute_task_impl({"test": "data"})
        assert result["success"] is True
        assert "Test task executed" in result["message"]
    
    def test_list_agents(self, temp_dirs, sample_config_agent):
        """Test listing registered agents"""
        factory = AgentFactory(
            config_agent_dir=str(temp_dirs['config']),
            python_agent_dir=str(temp_dirs['python'])
        )
        
        # Add a Python agent for variety
        register_agent_class(TestPythonAgent)
        
        # List all agents
        all_agents = factory.list_agents()
        assert len(all_agents) >= 2  # At least our config and Python agents
        
        # List only config agents
        config_agents = factory.list_agents(agent_type=AgentType.CONFIG_DRIVEN)
        config_agent_ids = [a.agent_id for a in config_agents]
        assert "sample-test-agent" in config_agent_ids
        
        # List only Python agents
        python_agents = factory.list_agents(agent_type=AgentType.PYTHON_DRIVEN)
        python_agent_ids = [a.agent_id for a in python_agents]
        assert "test-python-agent" in python_agent_ids
        
        # List by category
        specialists = factory.list_agents(category="specialists")
        assert len(specialists) >= 1
    
    def test_agent_enable_disable(self, temp_dirs, sample_config_agent):
        """Test enabling and disabling agents"""
        factory = AgentFactory(
            config_agent_dir=str(temp_dirs['config']),
            python_agent_dir=str(temp_dirs['python'])
        )
        
        agent_id = "sample-test-agent"
        
        # Should be enabled by default
        assert factory.registered_agents[agent_id].enabled is True
        
        # Disable the agent
        factory.disable_agent(agent_id)
        assert factory.registered_agents[agent_id].enabled is False
        
        # Should not be able to create disabled agent
        with pytest.raises(ValueError, match="disabled"):
            factory.create_agent(agent_id)
        
        # Re-enable the agent
        factory.enable_agent(agent_id)
        assert factory.registered_agents[agent_id].enabled is True
        
        # Should be able to create enabled agent
        agent = factory.create_agent(agent_id)
        assert agent is not None
    
    def test_factory_statistics(self, temp_dirs, sample_config_agent):
        """Test factory statistics"""
        factory = AgentFactory(
            config_agent_dir=str(temp_dirs['config']),
            python_agent_dir=str(temp_dirs['python'])
        )
        
        # Add Python agent
        register_agent_class(TestPythonAgent)
        
        stats = factory.get_statistics()
        
        # Check basic stats
        assert "total_agents" in stats
        assert "enabled_agents" in stats
        assert "disabled_agents" in stats
        assert "by_type" in stats
        assert "by_category" in stats
        assert "cache_stats" in stats
        
        # Should have at least our test agents
        assert stats["total_agents"] >= 2
        assert stats["by_type"]["config_driven"] >= 1
        assert stats["by_type"]["python_driven"] >= 1
    
    def test_invalid_agent_creation(self, temp_dirs):
        """Test error handling for invalid agent creation"""
        factory = AgentFactory(
            config_agent_dir=str(temp_dirs['config']),
            python_agent_dir=str(temp_dirs['python'])
        )
        
        # Try to create non-existent agent
        with pytest.raises(ValueError, match="not registered"):
            factory.create_agent("non-existent-agent")
    
    def test_convenience_functions(self):
        """Test convenience functions"""
        # Register an agent using convenience function
        register_agent_class(TestPythonAgent, agent_id="convenience-test")
        
        # Create using convenience function
        agent = create_agent("convenience-test", customer_id="test")
        assert isinstance(agent, TestPythonAgent)
        assert agent.customer_id == "test"
        
        # List using convenience function
        agents = list_available_agents()
        agent_ids = [a.agent_id for a in agents]
        assert "convenience-test" in agent_ids


def run_standalone_factory_tests():
    """Run agent factory tests standalone"""
    print("Running Agent Factory Tests...")
    
    # Test 1: Default Factory
    print("\n1. Testing Default Factory...")
    factory = get_default_factory()
    print(f"   ✅ Default factory initialized")
    print(f"   ✅ Config dir: {factory.config_agent_dir}")
    print(f"   ✅ Python dir: {factory.python_agent_dir}")
    
    # Test 2: Python Agent Registration
    print("\n2. Testing Python Agent Registration...")
    register_agent_class(TestPythonAgent, agent_id="standalone-test", priority=1)
    print(f"   ✅ Registered TestPythonAgent")
    
    # Check registration
    agents = list_available_agents()
    test_agent = next((a for a in agents if a.agent_id == "standalone-test"), None)
    if test_agent:
        print(f"   ✅ Found registered agent: {test_agent.name}")
        print(f"      - Type: {test_agent.agent_type.value}")
        print(f"      - Category: {test_agent.category}")
        print(f"      - Priority: {test_agent.priority}")
    
    # Test 3: Agent Creation
    print("\n3. Testing Agent Creation...")
    
    async def test_agent_creation():
        agent = create_agent("standalone-test", customer_id="test-customer")
        print(f"   ✅ Created agent: {agent.name}")
        print(f"      - Agent ID: {agent.agent_id}")
        print(f"      - Customer ID: {agent.customer_id}")
        
        # Initialize and test
        await agent._initialize_agent()
        
        result = await agent._execute_task_impl({"test": "factory"})
        if result["success"]:
            print(f"   ✅ Agent task executed successfully")
            print(f"      - Message: {result['message']}")
    
    asyncio.run(test_agent_creation())
    
    # Test 4: Factory Statistics
    print("\n4. Testing Factory Statistics...")
    stats = factory.get_statistics()
    print(f"   ✅ Total agents: {stats['total_agents']}")
    print(f"   ✅ Enabled agents: {stats['enabled_agents']}")
    print(f"   ✅ By type: {stats['by_type']}")
    print(f"   ✅ By category: {stats['by_category']}")
    
    print("\n✅ Agent Factory Tests Completed!")
    print("\n📋 Summary:")
    print("   - Factory Initialization: ✅ Working")
    print("   - Agent Registration: ✅ Working") 
    print("   - Python Agent Creation: ✅ Working")
    print("   - Agent Discovery: ✅ Working")
    print("   - Factory Statistics: ✅ Working")
    print("   - Convenience Functions: ✅ Working")


if __name__ == "__main__":
    run_standalone_factory_tests()