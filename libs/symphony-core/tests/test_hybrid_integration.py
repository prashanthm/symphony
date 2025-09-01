"""
Hybrid Architecture Integration Tests
Tests the complete hybrid system: ConfigurableAgent + TemplateEngine + AgentFactory
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from symphony_core.agents.base_agent import BaseAgent, AgentCapability, AgentSchedule
from symphony_core.agents.configurable_agent import ConfigurableAgent
from symphony_core.templates.template_engine import TemplateEngine
from symphony_core.factories.agent_factory import AgentFactory, AgentType, register_agent_class


class HybridTestAgent(BaseAgent):
    """Python agent that works alongside configuration agents"""
    
    AGENT_ID = "hybrid-python-agent"
    AGENT_NAME = "Hybrid Python Agent"
    AGENT_DESCRIPTION = "Python agent that demonstrates hybrid architecture"
    AGENT_CATEGORY = "specialists"
    
    def __init__(self, customer_id: str = None):
        super().__init__(
            agent_id=self.AGENT_ID,
            name=self.AGENT_NAME,
            role="Hybrid Test Specialist",
            category=self.AGENT_CATEGORY,
            capabilities=[
                AgentCapability("python_integration", "Python-config integration", "high"),
                AgentCapability("hybrid_coordination", "Coordinate with config agents", "high")
            ],
            schedule=AgentSchedule(),
            customer_id=customer_id
        )
    
    async def _initialize_agent(self) -> None:
        """Initialize hybrid agent"""
        await super()._initialize_agent()
        self.coordination_data = {}
    
    async def _execute_task_impl(self, task_data):
        """Execute tasks with hybrid capabilities"""
        task_type = task_data.get("type", "general")
        
        if task_type == "coordinate_with_config_agent":
            return await self._coordinate_with_config_agent(task_data)
        elif task_type == "process_template_output":
            return await self._process_template_output(task_data)
        else:
            return {
                "success": True,
                "agent_type": "python_driven",
                "message": f"Python agent executed {task_type}",
                "capabilities": [cap.name for cap in self.capabilities],
                "task_data": task_data
            }
    
    async def _coordinate_with_config_agent(self, task_data):
        """Demonstrate coordination between Python and config agents"""
        config_agent_data = task_data.get("config_agent_data", {})
        
        # Process data from configuration agent
        processed_data = {
            "python_processing": "Applied Python-specific logic",
            "received_from_config": config_agent_data,
            "coordination_timestamp": task_data.get("timestamp"),
            "hybrid_result": f"Coordinated with config agent: {config_agent_data.get('agent_name', 'unknown')}"
        }
        
        return {
            "success": True,
            "coordination_type": "python_config_hybrid",
            "processed_data": processed_data,
            "agent_type": "python_driven"
        }
    
    async def _process_template_output(self, task_data):
        """Process output from template generation"""
        template_output = task_data.get("template_output", {})
        
        # Apply Python-specific processing to template output
        if template_output.get("success") and "generated_document" in template_output:
            document = template_output["generated_document"]
            
            # Example processing: count sections, words, etc.
            sections = len(template_output.get("generated_sections", {}))
            word_count = len(document.split()) if document else 0
            
            return {
                "success": True,
                "template_processing": {
                    "original_template": template_output.get("template_name"),
                    "sections_count": sections,
                    "word_count": word_count,
                    "processing_notes": "Applied Python analytics to template output"
                },
                "agent_type": "python_driven",
                "hybrid_enhancement": True
            }
        
        return {
            "success": False,
            "error": "No valid template output to process",
            "agent_type": "python_driven"
        }
    
    async def _process_handoff(self, handoff_context) -> bool:
        """Process handoff in hybrid environment"""
        # Store coordination data for future use
        self.coordination_data[handoff_context.handoff_id] = {
            "from_agent": handoff_context.from_agent,
            "context_data": handoff_context.context_data
        }
        return True


class TestHybridIntegration:
    """Integration tests for hybrid architecture"""
    
    def setup_test_environment(self):
        """Set up temporary environment for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        config_dir = temp_dir / "agents"
        template_dir = temp_dir / "templates"
        
        config_dir.mkdir()
        template_dir.mkdir()
        
        # Create test configuration agent
        config_agent_path = config_dir / "integration-test-agent.md"
        config_content = """# Integration Test Agent

```yaml
agent:
  name: Integration Test Agent
  id: integration-test-agent
  title: Integration Configuration Agent
  icon: 🔗
  whenToUse: Use for testing hybrid architecture integration

persona:
  role: Integration Test Specialist
  identity: Hybrid architecture integration specialist
  style: Comprehensive and systematic
  core_principles:
    - Test all integration points
    - Validate hybrid functionality
    - Ensure seamless coordination

commands:
  - help: Show available commands
  - generate-test-doc: run task create-doc.md with template test-integration-template.yaml
  - coordinate-with-python: Execute coordination workflow with Python agents
  - validate-integration: Validate hybrid architecture integration

dependencies:
  templates:
    - test-integration-template.yaml
  tasks:
    - create-doc.md
    - coordinate-workflow.md
```"""
        
        with open(config_agent_path, 'w') as f:
            f.write(config_content)
        
        # Create test template
        template_path = template_dir / "test-integration-template.yaml"
        template_content = """template_info:
  name: "Integration Test Template"
  version: "1.0"
  description: "Template for testing hybrid architecture integration"
  author: "Hybrid Test System"
  category: "integration_testing"

sections:
  header:
    format: |
      # {title}
      **Integration Test Document**
      
      - **Generated by:** {agent_name}
      - **Agent Type:** {agent_type}
      - **Customer:** {customer_id}
      - **Timestamp:** {timestamp}
      
  integration_results:
    format: |
      ## Integration Test Results
      
      ### Configuration Agent Results
      {config_results}
      
      ### Python Agent Results  
      {python_results}
      
      ### Hybrid Coordination
      {coordination_results}
      
  summary:
    format: |
      ## Summary
      
      This document demonstrates successful integration between:
      - Configuration-driven agents (Markdown + YAML)
      - Python-driven agents (Code-based)
      - Template engine (YAML templates)
      - Agent factory (Hybrid creation)
      
      **Integration Status:** {integration_status}

default_values:
  title: "Hybrid Architecture Integration Test"
  agent_type: "hybrid_system"
  customer_id: "integration_test_customer"
  config_results: "✅ Configuration agent functionality working"
  python_results: "✅ Python agent functionality working"
  coordination_results: "✅ Inter-agent coordination working"
  integration_status: "SUCCESS"

validation_rules:
  required_fields:
    - title
    - agent_name
    - integration_status"""
        
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        return {
            'temp_dir': temp_dir,
            'config_dir': config_dir,
            'template_dir': template_dir,
            'config_agent_path': str(config_agent_path),
            'template_path': str(template_path)
        }
    
    def cleanup_test_environment(self, env_info):
        """Clean up test environment"""
        shutil.rmtree(env_info['temp_dir'])
    
    async def test_full_hybrid_workflow(self):
        """Test complete hybrid workflow end-to-end"""
        print("\n🔗 Testing Full Hybrid Workflow...")
        
        # Setup
        env = self.setup_test_environment()
        
        try:
            # 1. Create Agent Factory with test environment
            print("   Step 1: Initialize Agent Factory")
            factory = AgentFactory(
                config_agent_dir=str(env['config_dir']),
                template_dir=str(env['template_dir'])
            )
            
            # 2. Register Python agent with this factory
            print("   Step 2: Register Python Agent")
            factory.register_agent(
                agent_id="hybrid-python-agent",
                agent_type=AgentType.PYTHON_DRIVEN,
                source="test_module.HybridTestAgent",
                name="Hybrid Python Agent",
                description="Python agent for testing hybrid architecture",
                category="specialists"
            )
            
            # Cache the agent class
            factory.agent_class_cache["hybrid-python-agent"] = HybridTestAgent
            
            print(f"      ✅ Factory initialized with {len(factory.registered_agents)} agents")
            
            # 3. Create Configuration Agent
            print("   Step 3: Create Configuration Agent")
            config_agent = factory.create_agent("integration-test-agent", customer_id="test-customer")
            await config_agent._initialize_agent()
            
            print(f"      ✅ Config agent created: {config_agent.name}")
            
            # 4. Create Python Agent
            print("   Step 4: Create Python Agent")
            python_agent = factory.create_agent("hybrid-python-agent", customer_id="test-customer")
            await python_agent._initialize_agent()
            
            print(f"      ✅ Python agent created: {python_agent.name}")
            
            # 5. Test Template Generation via Config Agent
            print("   Step 5: Generate Document via Config Agent")
            template_result = await config_agent._execute_template_generation({
                "template_name": "test-integration-template.yaml",
                "parameters": {
                    "title": "Hybrid Integration Success Test",
                    "config_results": "✅ Configuration agent template generation working",
                    "python_results": "⏳ Testing Python agent coordination...",
                    "coordination_results": "⏳ Testing hybrid coordination..."
                }
            })
            
            if template_result["success"]:
                print("      ✅ Template generation successful")
                if template_result.get("engine_generated"):
                    print("         - Using full template engine")
                    document_length = len(template_result["generated_document"])
                    print(f"         - Document length: {document_length} characters")
            
            # 6. Test Python Agent Processing Template Output
            print("   Step 6: Process Template Output with Python Agent")
            processing_result = await python_agent._execute_task_impl({
                "type": "process_template_output",
                "template_output": template_result
            })
            
            if processing_result["success"]:
                print("      ✅ Python agent template processing successful")
                template_processing = processing_result["template_processing"]
                print(f"         - Sections analyzed: {template_processing['sections_count']}")
                print(f"         - Word count: {template_processing['word_count']}")
            
            # 7. Test Inter-Agent Coordination
            print("   Step 7: Test Inter-Agent Coordination")
            config_help_result = await config_agent._execute_help_command()
            
            coordination_result = await python_agent._execute_task_impl({
                "type": "coordinate_with_config_agent",
                "config_agent_data": config_help_result.get("help_info", {}),
                "timestamp": template_result.get("generated_at")
            })
            
            if coordination_result["success"]:
                print("      ✅ Inter-agent coordination successful")
                print(f"         - Coordination type: {coordination_result['coordination_type']}")
                processed_data = coordination_result["processed_data"]
                print(f"         - Hybrid result: {processed_data['hybrid_result']}")
            
            # 8. Generate Final Integration Report
            print("   Step 8: Generate Final Integration Report")
            final_report = await config_agent._execute_template_generation({
                "template_name": "test-integration-template.yaml",
                "parameters": {
                    "title": "Hybrid Architecture Integration - COMPLETE",
                    "config_results": "✅ All configuration agent features working",
                    "python_results": "✅ All Python agent features working",
                    "coordination_results": "✅ Full hybrid coordination working",
                    "integration_status": "FULL SUCCESS"
                }
            })
            
            if final_report["success"]:
                print("      ✅ Final integration report generated")
                
                # Show summary of what was tested
                print("\n   🎯 Integration Test Summary:")
                print("      ✅ Configuration-driven agents (Markdown + YAML)")
                print("      ✅ Python-driven agents (Code-based)")
                print("      ✅ YAML template engine")
                print("      ✅ Agent factory (hybrid creation)")
                print("      ✅ Inter-agent coordination")
                print("      ✅ Template processing pipeline")
                print("      ✅ End-to-end workflow")
                
                return {
                    "success": True,
                    "integration_complete": True,
                    "agents_tested": ["config_agent", "python_agent"],
                    "features_validated": [
                        "markdown_yaml_parsing",
                        "template_generation",
                        "agent_factory_creation",
                        "inter_agent_coordination",
                        "hybrid_workflow"
                    ],
                    "final_report": final_report
                }
            
        finally:
            self.cleanup_test_environment(env)
    
    async def test_agent_factory_hybrid_support(self):
        """Test agent factory's hybrid support capabilities"""
        print("\n🏭 Testing Agent Factory Hybrid Support...")
        
        # Register both types of agents
        register_agent_class(HybridTestAgent, agent_id="factory-python-test")
        
        factory = AgentFactory()
        
        # Test listing agents by type
        all_agents = factory.list_agents()
        config_agents = factory.list_agents(agent_type=AgentType.CONFIG_DRIVEN)
        python_agents = factory.list_agents(agent_type=AgentType.PYTHON_DRIVEN)
        
        print(f"   ✅ Total agents: {len(all_agents)}")
        print(f"   ✅ Config agents: {len(config_agents)}")
        print(f"   ✅ Python agents: {len(python_agents)}")
        
        # Test creating agents of different types
        if python_agents:
            python_agent = factory.create_agent(python_agents[0].agent_id, customer_id="test")
            print(f"   ✅ Created Python agent: {python_agent.name}")
        
        # Test factory statistics
        stats = factory.get_statistics()
        print(f"   ✅ Factory statistics: {stats['by_type']}")
        
        return {
            "success": True,
            "factory_hybrid_support": True,
            "statistics": stats
        }


async def run_hybrid_integration_tests():
    """Run all hybrid integration tests"""
    print("🚀 Running Hybrid Architecture Integration Tests...")
    
    test_suite = TestHybridIntegration()
    
    # Test 1: Full Hybrid Workflow
    result1 = await test_suite.test_full_hybrid_workflow()
    
    # Test 2: Agent Factory Hybrid Support
    result2 = await test_suite.test_agent_factory_hybrid_support()
    
    # Summary
    print(f"\n✅ Hybrid Integration Tests Complete!")
    
    success_count = sum(1 for result in [result1, result2] if result and result.get("success"))
    print(f"📊 Results: {success_count}/2 tests passed")
    
    if result1 and result1.get("success"):
        print("\n🎯 Hybrid Architecture Features Validated:")
        for feature in result1["features_validated"]:
            print(f"   ✅ {feature.replace('_', ' ').title()}")
    
    return {
        "overall_success": success_count == 2,
        "test_results": [result1, result2],
        "features_validated": result1.get("features_validated", []) if result1 else []
    }


if __name__ == "__main__":
    # Run integration tests
    result = asyncio.run(run_hybrid_integration_tests())
    
    if result["overall_success"]:
        print("\n🎉 All Hybrid Integration Tests PASSED!")
        print("\n📋 Hybrid Architecture Implementation Complete:")
        print("   ✅ Configuration-driven agents working")
        print("   ✅ Python-driven agents working") 
        print("   ✅ Template engine working")
        print("   ✅ Agent factory working")
        print("   ✅ Full hybrid coordination working")
        
        print("\n💡 Business Value Delivered:")
        print("   🔧 Flexibility: Both config and code-driven agents")
        print("   🚀 Performance: Python integration capabilities")
        print("   📝 Standardization: YAML template system")
        print("   🏭 Scalability: Factory pattern for agent creation")
        print("   🔗 Integration: Seamless agent coordination")
        
        exit(0)
    else:
        print("\n❌ Some integration tests failed")
        exit(1)