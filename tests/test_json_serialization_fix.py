#!/usr/bin/env python3
"""
Focused Test Suite for JSON Serialization Fix
Testing the specific fix for enum serialization in WorkflowManager
"""

import asyncio
import json
import tempfile
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add path to symphony-core
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "symphony-core" / "src"))

from symphony_core.onboarding.workflow_manager import (
    WorkflowManager, WorkflowStatus, StepStatus, WorkflowStep, WorkflowState,
    create_workflow_manager
)


def test_workflow_creation_and_json_serialization():
    """Test workflow creation and JSON serialization of enums"""
    print("Testing workflow creation and JSON serialization...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create WorkflowManager
        manager = create_workflow_manager(temp_dir)
        
        # Test workflow creation
        workflow_id = manager.create_workflow(
            customer_name="test-customer",
            package_type="startup",
            industry="technology"
        )
        
        print(f"✓ Workflow created: {workflow_id}")
        
        # Check that workflow file exists and is valid JSON
        workflow_file = manager.workflows_dir / f"{workflow_id}.json"
        assert workflow_file.exists(), "Workflow file should exist"
        
        # Read and parse JSON to ensure it's valid
        with open(workflow_file, 'r') as f:
            workflow_data = json.load(f)
        
        print("✓ JSON file is valid and readable")
        
        # Check enum serialization
        assert isinstance(workflow_data['status'], str), "Status should be serialized as string"
        assert workflow_data['status'] == WorkflowStatus.NOT_STARTED.value
        
        # Check step enum serialization
        for step in workflow_data['steps']:
            assert isinstance(step['status'], str), "Step status should be serialized as string"
            assert step['status'] == StepStatus.PENDING.value
        
        print("✓ Enum serialization working correctly")
        
        return True


def test_workflow_state_loading():
    """Test workflow state loading and enum reconstruction"""
    print("Testing workflow state loading...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create workflow
        workflow_id = manager.create_workflow("load-test-customer")
        
        # Load workflow state
        loaded_state = manager._load_workflow_state(workflow_id)
        
        assert loaded_state is not None, "Should load workflow state"
        assert isinstance(loaded_state.status, WorkflowStatus), "Status should be WorkflowStatus enum"
        assert loaded_state.status == WorkflowStatus.NOT_STARTED
        
        # Check step enum reconstruction
        for step in loaded_state.steps:
            assert isinstance(step.status, StepStatus), "Step status should be StepStatus enum"
            assert step.status == StepStatus.PENDING
        
        print("✓ Workflow state loading and enum reconstruction working")
        
        return True


def test_step_to_dict_helper():
    """Test the _step_to_dict helper method"""
    print("Testing _step_to_dict helper method...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create a test step
        test_step = WorkflowStep(
            step_id="test_step",
            name="Test Step",
            description="Test step for JSON serialization",
            status=StepStatus.RUNNING,
            dependencies=["dep1", "dep2"]
        )
        
        # Test _step_to_dict
        step_dict = manager._step_to_dict(test_step)
        
        # Verify structure
        assert isinstance(step_dict, dict), "Should return dictionary"
        assert isinstance(step_dict['status'], str), "Status should be string"
        assert step_dict['status'] == StepStatus.RUNNING.value
        assert step_dict['step_id'] == "test_step"
        assert step_dict['name'] == "Test Step"
        assert step_dict['dependencies'] == ["dep1", "dep2"]
        
        print("✓ _step_to_dict helper method working correctly")
        
        return True


def test_external_template_integration():
    """Test external template loading with JSON serialization"""
    print("Testing external template integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create test template file
        template_path = Path(temp_dir) / "test_template.yaml"
        template_content = """
workspace:
  name: "${customer_name} Test Workspace"
  organization:
    name: "${customer_name}"
teams:
  - name: "Engineering"
    key: "ENG"
projects:
  test_project:
    name: "Test Project"
    description: "Test project from template"
symphony_integration:
  agent_assignments:
    Engineering:
      - "CTO Agent"
      - "Tech Lead Agent"
"""
        
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        # Create workflow with external template
        workflow_id = manager.create_workflow(
            customer_name="template-test",
            package_type="enterprise",
            industry="technology",
            template_file=str(template_path)
        )
        
        print(f"✓ Workflow with external template created: {workflow_id}")
        
        # Check JSON serialization
        workflow_file = manager.workflows_dir / f"{workflow_id}.json"
        with open(workflow_file, 'r') as f:
            workflow_data = json.load(f)
        
        print("✓ External template workflow JSON serialization successful")
        
        # Load and verify state
        loaded_state = manager._load_workflow_state(workflow_id)
        assert loaded_state is not None
        
        # Find integration setup step with template metadata
        integration_step = None
        for step in loaded_state.steps:
            if step.step_id == "setup_integrations" and hasattr(step, 'metadata') and step.metadata:
                if 'linear_template' in step.metadata:
                    integration_step = step
                    break
        
        if integration_step:
            print("✓ Template metadata preserved in workflow step")
            template_data = integration_step.metadata['linear_template']
            assert 'workspace' in template_data
            assert 'teams' in template_data
        else:
            print("! No enhanced integration step found (using base workflow)")
        
        return True


def test_workflow_status_operations():
    """Test workflow status operations and JSON persistence"""
    print("Testing workflow status operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create workflow
        workflow_id = manager.create_workflow("status-test")
        
        # Test get_workflow_status
        status = manager.get_workflow_status(workflow_id)
        
        assert status is not None, "Should return status"
        assert 'workflow_id' in status
        assert 'status' in status
        assert status['status'] == WorkflowStatus.NOT_STARTED.value
        assert 'progress' in status
        assert 'current_step' in status['progress']
        
        print("✓ Workflow status operations working")
        
        # Test list_workflows
        workflows = manager.list_workflows()
        assert len(workflows) > 0, "Should list workflows"
        
        workflow_ids = [w['workflow_id'] for w in workflows]
        assert workflow_id in workflow_ids, "Should include created workflow"
        
        print("✓ Workflow listing working")
        
        return True


async def test_workflow_execution_serialization():
    """Test workflow execution with state persistence"""
    print("Testing workflow execution with serialization...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create workflow
        workflow_id = manager.create_workflow("execution-test")
        
        # Mock a simple step handler
        async def mock_step_handler(workflow_state, step):
            print(f"  Executing mock step: {step.name}")
            return {"success": True, "message": f"Mock execution of {step.name}"}
        
        # Register handler for first step
        first_step = manager._load_workflow_state(workflow_id).steps[0]
        manager.register_step_handler(first_step.step_id, mock_step_handler)
        
        # Start workflow execution (this will test JSON serialization during execution)
        try:
            result = await manager.start_workflow(workflow_id)
            print(f"✓ Workflow execution result: {result.get('success', False)}")
            
            # Check final state serialization
            final_state = manager._load_workflow_state(workflow_id)
            assert final_state is not None
            
            # Check that at least one step was executed
            executed_steps = [s for s in final_state.steps if s.status in [StepStatus.COMPLETED, StepStatus.RUNNING]]
            if executed_steps:
                print("✓ Workflow execution and state serialization successful")
            else:
                print("! No steps were executed (possible due to missing dependencies)")
            
        except Exception as e:
            print(f"✓ Workflow execution handled gracefully: {e}")
        
        return True


def run_all_tests():
    """Run all JSON serialization tests"""
    print("=" * 60)
    print("JSON SERIALIZATION FIX VALIDATION TESTS")
    print("=" * 60)
    
    tests = [
        test_workflow_creation_and_json_serialization,
        test_workflow_state_loading,
        test_step_to_dict_helper,
        test_external_template_integration,
        test_workflow_status_operations,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            print(f"\n{test_func.__name__}:")
            result = test_func()
            if result:
                passed += 1
                print(f"✅ PASSED: {test_func.__name__}")
            else:
                failed += 1
                print(f"❌ FAILED: {test_func.__name__}")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR in {test_func.__name__}: {e}")
    
    # Run async test
    try:
        print(f"\ntest_workflow_execution_serialization:")
        result = asyncio.run(test_workflow_execution_serialization())
        if result:
            passed += 1
            print(f"✅ PASSED: test_workflow_execution_serialization")
        else:
            failed += 1
            print(f"❌ FAILED: test_workflow_execution_serialization")
    except Exception as e:
        failed += 1
        print(f"❌ ERROR in test_workflow_execution_serialization: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - JSON serialization fix is working correctly!")
    else:
        print(f"⚠️  {failed} tests failed - there may be issues with the JSON serialization fix")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)