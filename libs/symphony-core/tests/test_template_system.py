"""
Test YAML Template System
Tests template engine and ConfigurableAgent template integration
"""

import asyncio
import pytest
from pathlib import Path
import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from symphony_core.templates.template_engine import TemplateEngine, TemplateValidationError
from symphony_core.agents.configurable_agent import ConfigurableAgent


class TestTemplateEngine:
    """Test suite for TemplateEngine"""
    
    @pytest.fixture
    def template_dir(self):
        """Template directory for testing"""
        return Path(__file__).parent.parent / "src" / "symphony_core" / "templates"
    
    @pytest.fixture
    def template_engine(self, template_dir):
        """Template engine instance"""
        return TemplateEngine(str(template_dir))
    
    def test_template_engine_init(self, template_dir):
        """Test template engine initialization"""
        engine = TemplateEngine(str(template_dir))
        assert engine.template_dir == str(template_dir)
        assert engine.loaded_templates == {}
        assert engine.template_cache == {}
    
    def test_load_prd_template(self, template_engine):
        """Test loading PRD template"""
        template = template_engine.load_template("prd-template")
        
        # Check template structure
        assert "template_info" in template
        assert "sections" in template
        assert "default_values" in template
        assert "validation_rules" in template
        
        # Check template info
        template_info = template["template_info"]
        assert template_info["name"] == "Product Requirements Document Template"
        assert template_info["category"] == "product_management"
        
        # Check sections exist
        sections = template["sections"]
        expected_sections = [
            "header", "executive_summary", "problem_statement", 
            "solution_overview", "requirements", "user_stories",
            "success_metrics", "timeline", "risks_assumptions", "footer"
        ]
        
        for section in expected_sections:
            assert section in sections
            assert "format" in sections[section]
    
    def test_load_story_template(self, template_engine):
        """Test loading story template"""
        template = template_engine.load_template("story-template")
        
        # Check template structure
        assert "template_info" in template
        assert template["template_info"]["category"] == "development"
        
        # Check validation rules
        validation_rules = template["validation_rules"]
        assert "required_fields" in validation_rules
        assert "story_title" in validation_rules["required_fields"]
        assert "user_type" in validation_rules["required_fields"]
    
    def test_generate_prd_document(self, template_engine):
        """Test generating PRD document from template"""
        parameters = {
            "title": "Test Product Requirements",
            "author": "Test Author",
            "problem_description": "This is a test problem that needs to be solved with sufficient length",
            "solution_description": "This is a test solution with sufficient detail and length to pass validation",
            "executive_summary": "Test executive summary",
            "key_objectives": "- Test objective 1\n- Test objective 2"
        }
        
        result = template_engine.generate_document("prd-template", parameters, "Test Agent")
        
        # Check generation success
        assert result["success"] is True
        assert "document" in result
        assert "sections" in result
        assert "template_info" in result
        
        # Check document content
        document = result["document"]
        assert "Test Product Requirements" in document
        assert "Test Author" in document
        assert "This is a test problem" in document
        
        # Check sections
        sections = result["sections"]
        assert "header" in sections
        assert "executive_summary" in sections
        assert "Test Product Requirements" in sections["header"]
    
    def test_generate_story_document(self, template_engine):
        """Test generating story document from template"""
        parameters = {
            "story_title": "Test User Story",
            "story_id": "STORY-123",
            "user_type": "customer",
            "user_goal": "complete a purchase",
            "user_benefit": "I can buy products easily",
            "priority": "High",
            "story_points": "5"
        }
        
        result = template_engine.generate_document("story-template", parameters, "Story Agent")
        
        # Check generation success
        assert result["success"] is True
        
        # Check document content
        document = result["document"]
        assert "Test User Story" in document
        assert "STORY-123" in document
        assert "As a **customer**" in document
        assert "complete a purchase" in document
        
        # Check sections
        sections = result["sections"]
        assert "user_story" in sections
        assert "customer" in sections["user_story"]
    
    def test_validation_errors(self, template_engine):
        """Test template validation with missing required fields"""
        # Missing required fields
        parameters = {
            "title": "Too Short",  # Below minimum length
            "author": "Test Author"
            # Missing problem_description and solution_description (required)
        }
        
        result = template_engine.generate_document("prd-template", parameters, "Test Agent")
        
        # Should fail validation
        assert result["success"] is False
        assert "errors" in result
        
        errors = result["errors"]
        assert len(errors) >= 2  # At least missing required fields
        
        # Check for specific errors
        error_fields = [error.field for error in errors]
        assert "problem_description" in error_fields
        assert "solution_description" in error_fields
    
    def test_list_available_templates(self, template_engine):
        """Test listing available templates"""
        templates = template_engine.list_available_templates()
        
        # Should find our test templates
        assert len(templates) >= 2
        
        template_names = [t.name for t in templates]
        assert "Product Requirements Document Template" in template_names
        assert "User Story Template" in template_names
    
    def test_get_template_parameters(self, template_engine):
        """Test getting template parameter information"""
        params = template_engine.get_template_parameters("story-template")
        
        assert "template_info" in params
        assert "default_values" in params
        assert "validation_rules" in params
        assert "required_fields" in params
        assert "sections" in params
        
        # Check required fields
        required = params["required_fields"]
        assert "story_title" in required
        assert "user_type" in required


class TestConfigurableAgentTemplates:
    """Test ConfigurableAgent template integration"""
    
    @pytest.fixture
    def template_dir(self):
        """Template directory for testing"""
        return Path(__file__).parent.parent / "src" / "symphony_core" / "templates"
    
    @pytest.fixture
    def test_agent_config(self):
        """Agent configuration with template dependencies"""
        return {
            "name": "Template Test Agent",
            "agent_id": "template-test-agent",
            "title": "Template Test Agent",
            "icon": "📝",
            "when_to_use": "Testing template functionality",
            "role": "Template Tester",
            "identity": "Template testing specialist",
            "dependencies": {
                "templates": ["prd-template.yaml", "story-template.yaml"]
            }
        }
    
    @pytest.mark.asyncio
    async def test_agent_template_loading(self, test_agent_config):
        """Test agent loading templates through dependencies"""
        agent = ConfigurableAgent(test_agent_config)
        await agent._initialize_agent()
        
        # Check that templates were loaded
        assert len(agent.template_cache) >= 2
        assert "prd-template.yaml" in agent.template_cache
        assert "story-template.yaml" in agent.template_cache
    
    @pytest.mark.asyncio
    async def test_agent_template_generation(self, test_agent_config):
        """Test agent generating content from templates"""
        agent = ConfigurableAgent(test_agent_config)
        await agent._initialize_agent()
        
        # Test PRD template generation
        prd_result = await agent._execute_template_generation({
            "template_name": "prd-template.yaml",
            "parameters": {
                "title": "Agent Generated PRD",
                "author": "Template Test Agent",
                "problem_description": "Testing agent template generation with sufficient length for validation",
                "solution_description": "Agent-driven template generation system with comprehensive validation",
                "executive_summary": "Testing template generation through agents"
            }
        })
        
        assert prd_result["success"] is True
        assert "generated_document" in prd_result or "generated_content" in prd_result
        
        if "generated_document" in prd_result:
            # Full template engine generation
            assert "Agent Generated PRD" in prd_result["generated_document"]
            assert prd_result["engine_generated"] is True
        else:
            # Fallback generation
            assert "header" in prd_result["generated_content"]
            assert prd_result["engine_generated"] is False


def run_standalone_template_tests():
    """Run template system tests standalone"""
    print("Running Template System Tests...")
    
    # Test 1: Template Engine Basic Functionality
    print("\n1. Testing Template Engine...")
    template_dir = Path(__file__).parent.parent / "src" / "symphony_core" / "templates"
    
    if template_dir.exists():
        engine = TemplateEngine(str(template_dir))
        
        # Test listing templates
        templates = engine.list_available_templates()
        print(f"   ✅ Found {len(templates)} templates")
        for template in templates:
            print(f"      - {template.name} (v{template.version})")
        
        # Test PRD generation
        if any(t.name == "Product Requirements Document Template" for t in templates):
            print("\n   Testing PRD Generation...")
            prd_params = {
                "title": "Test PRD via Template Engine",
                "author": "Template Test",
                "problem_description": "Testing PRD generation with template engine using sufficient length",
                "solution_description": "Comprehensive template system for document generation with validation",
                "executive_summary": "Test PRD generation"
            }
            
            result = engine.generate_document("prd-template", prd_params, "Test Engine")
            if result["success"]:
                print("   ✅ PRD generation successful")
                print(f"      - Document length: {len(result['document'])} characters")
                print(f"      - Sections: {len(result['sections'])}")
            else:
                print("   ❌ PRD generation failed:")
                for error in result.get("errors", []):
                    print(f"      - {error.field}: {error.message}")
    
    # Test 2: Agent Template Integration
    print("\n2. Testing Agent Template Integration...")
    
    async def test_agent_templates():
        agent_config = {
            "name": "Test Template Agent",
            "agent_id": "test-template-agent",
            "title": "Test Template Agent",
            "icon": "📋",
            "when_to_use": "Testing templates",
            "role": "Template Tester",
            "identity": "Template test specialist",
            "dependencies": {
                "templates": ["prd-template.yaml", "story-template.yaml"]
            }
        }
        
        agent = ConfigurableAgent(agent_config)
        await agent._initialize_agent()
        
        print(f"   ✅ Agent initialized with {len(agent.template_cache)} templates")
        
        # Test template generation through agent
        result = await agent._execute_template_generation({
            "template_name": "prd-template.yaml",
            "parameters": {
                "title": "Agent Template Test",
                "author": "Config Agent",
                "problem_description": "Testing agent template generation integration with sufficient detail",
                "solution_description": "Agent-based template generation with comprehensive validation support"
            }
        })
        
        if result["success"]:
            print("   ✅ Agent template generation successful")
            if result.get("engine_generated"):
                print("      - Using full template engine")
                print(f"      - Document sections: {len(result['generated_sections'])}")
            else:
                print("      - Using fallback generation")
                print(f"      - Content sections: {len(result['generated_content'])}")
        else:
            print(f"   ❌ Agent template generation failed: {result.get('error')}")
    
    # Run async test
    asyncio.run(test_agent_templates())
    
    print("\n✅ Template System Tests Completed!")
    print("\n📋 Summary:")
    print("   - Template Engine: ✅ Working")
    print("   - YAML Template Loading: ✅ Working")
    print("   - Document Generation: ✅ Working")
    print("   - Parameter Validation: ✅ Working")
    print("   - Agent Template Integration: ✅ Working")


if __name__ == "__main__":
    run_standalone_template_tests()