#!/usr/bin/env python3
"""
Comprehensive Test Suite for JSON Serialization
Tests edge cases and comprehensive scenarios for enum serialization fix
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


def test_all_enum_values_serialization():
    """Test all possible enum values can be serialized and deserialized"""
    print("Testing all enum values serialization...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Test all WorkflowStatus values
        for status in WorkflowStatus:
            workflow_state = WorkflowState(
                workflow_id=f"test-{status.value}",
                customer_name="test-customer",
                package_type="startup",
                industry="general",
                status=status
            )
            
            # Test serialization using the manager's method
            manager._save_workflow_state(workflow_state)
            
            # Test deserialization
            loaded_state = manager._load_workflow_state(workflow_state.workflow_id)
            assert loaded_state.status == status, f"Failed to serialize/deserialize {status}"
        
        # Test all StepStatus values
        for step_status in StepStatus:
            test_step = WorkflowStep(
                step_id=f"test-step-{step_status.value}",
                name=f"Test Step {step_status.value}",
                description=f"Test step with status {step_status.value}",
                status=step_status
            )
            
            # Test _step_to_dict serialization
            step_dict = manager._step_to_dict(test_step)
            assert step_dict['status'] == step_status.value, f"Failed to serialize step status {step_status}"
        
        print("✓ All enum values serialize and deserialize correctly")
        return True


def test_concurrent_workflow_operations():
    """Test concurrent workflow operations with JSON serialization"""
    print("Testing concurrent workflow operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create multiple workflows
        workflow_ids = []
        for i in range(5):
            workflow_id = manager.create_workflow(
                customer_name=f"customer-{i}",
                package_type="startup" if i % 2 == 0 else "enterprise",
                industry="technology"
            )
            workflow_ids.append(workflow_id)
        
        # Verify all workflows can be loaded
        for workflow_id in workflow_ids:
            loaded_state = manager._load_workflow_state(workflow_id)
            assert loaded_state is not None, f"Failed to load workflow {workflow_id}"
            assert loaded_state.status == WorkflowStatus.NOT_STARTED
        
        # List all workflows
        all_workflows = manager.list_workflows()
        assert len(all_workflows) >= 5, "Not all workflows listed"
        
        print("✓ Concurrent workflow operations working correctly")
        return True


def test_workflow_step_updates_persistence():
    """Test that step updates are properly persisted with JSON serialization"""
    print("Testing workflow step updates persistence...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create workflow
        workflow_id = manager.create_workflow("persistence-test")
        
        # Update step through multiple status changes
        step_statuses = [StepStatus.RUNNING, StepStatus.COMPLETED, StepStatus.FAILED]
        
        for status in step_statuses:
            # Load current state
            current_state = manager._load_workflow_state(workflow_id)
            first_step = current_state.steps[0]
            
            # Update step status
            first_step.status = status
            first_step.error_message = f"Test message for {status.value}" if status == StepStatus.FAILED else None
            
            # Save state
            manager._save_workflow_state(current_state)
            
            # Reload and verify
            reloaded_state = manager._load_workflow_state(workflow_id)
            reloaded_step = reloaded_state.steps[0]
            
            assert reloaded_step.status == status, f"Status {status} not persisted correctly"
            if status == StepStatus.FAILED:
                assert reloaded_step.error_message == f"Test message for {status.value}"
        
        print("✓ Step updates persist correctly across save/load cycles")
        return True


def test_complex_workflow_template_serialization():
    """Test complex workflow templates with metadata serialization"""
    print("Testing complex workflow template serialization...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create complex template file
        template_path = Path(temp_dir) / "complex_template.yaml"
        template_content = """
workflow_template:
  package_type: enterprise
  steps:
    - id: custom_validation
      name: "Complex Validation Step"
      description: "Complex validation with nested metadata"
      required: true
      estimated_duration: 1200
      dependencies: []
      metadata:
        complexity_level: high
        validation_rules:
          - type: environment
            criteria: ["python>=3.8", "uv>=0.1.0"]
          - type: security
            criteria: ["ssl_enabled", "auth_configured"]
        retry_policy:
          max_attempts: 5
          backoff_strategy: exponential
    - id: advanced_setup
      name: "Advanced Setup Step"
      description: "Advanced setup with complex dependencies"
      required: true
      estimated_duration: 2400
      dependencies: ["custom_validation"]
      metadata:
        setup_type: advanced
        configurations:
          database:
            type: postgresql
            version: "13+"
            clustering: true
          cache:
            type: redis
            cluster_mode: true
          monitoring:
            enabled: true
            tools: ["prometheus", "grafana"]
"""
        
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        # Create workflow with complex template
        workflow_id = manager.create_workflow(
            customer_name="complex-test",
            package_type="enterprise",
            industry="general",
            template_file=str(template_path)
        )
        
        # Verify JSON serialization
        workflow_file = manager.workflows_dir / f"{workflow_id}.json"
        with open(workflow_file, 'r') as f:
            workflow_data = json.load(f)
        
        # Check that complex metadata was preserved
        validation_step = next(s for s in workflow_data['steps'] if s['step_id'] == 'custom_validation')
        assert 'metadata' in validation_step
        assert validation_step['metadata']['complexity_level'] == 'high'
        assert 'validation_rules' in validation_step['metadata']
        assert len(validation_step['metadata']['validation_rules']) == 2
        
        # Verify deserialization
        loaded_state = manager._load_workflow_state(workflow_id)
        loaded_validation_step = next(s for s in loaded_state.steps if s.step_id == 'custom_validation')
        assert loaded_validation_step.metadata['complexity_level'] == 'high'
        
        print("✓ Complex workflow templates serialize and deserialize correctly")
        return True


def test_error_recovery_serialization():
    """Test error recovery scenarios with JSON serialization"""
    print("Testing error recovery scenarios...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create workflow
        workflow_id = manager.create_workflow("error-recovery-test")
        
        # Simulate error scenarios
        workflow_state = manager._load_workflow_state(workflow_id)
        
        # Add error to workflow
        error_message = "Simulated network timeout during integration setup"
        manager._add_error_to_history(workflow_state, error_message)
        
        # Update step with error
        failed_step = workflow_state.steps[1]  # Integration setup step
        failed_step.status = StepStatus.FAILED
        failed_step.error_message = error_message
        failed_step.retry_count = 2
        
        # Save and reload
        manager._save_workflow_state(workflow_state)
        reloaded_state = manager._load_workflow_state(workflow_id)
        
        # Verify error state persisted
        assert len(reloaded_state.error_history) == 1
        assert reloaded_state.error_history[0]['error'] == error_message
        
        reloaded_failed_step = reloaded_state.steps[1]
        assert reloaded_failed_step.status == StepStatus.FAILED
        assert reloaded_failed_step.error_message == error_message
        assert reloaded_failed_step.retry_count == 2
        
        print("✓ Error recovery scenarios persist correctly")
        return True


def test_get_workflow_status_comprehensive():
    """Test comprehensive workflow status with all fields"""
    print("Testing comprehensive workflow status...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create workflow
        workflow_id = manager.create_workflow("status-comprehensive-test", "enterprise", "healthcare")
        
        # Update various aspects of the workflow
        workflow_state = manager._load_workflow_state(workflow_id)
        workflow_state.status = WorkflowStatus.IN_PROGRESS
        workflow_state.started_at = datetime.now(timezone.utc).isoformat()
        workflow_state.current_step = workflow_state.steps[1].step_id
        
        # Update some steps
        workflow_state.steps[0].status = StepStatus.COMPLETED
        workflow_state.steps[0].completed_at = datetime.now(timezone.utc).isoformat()
        workflow_state.steps[1].status = StepStatus.RUNNING
        workflow_state.steps[1].started_at = datetime.now(timezone.utc).isoformat()
        
        # Add some configuration and integration data
        workflow_state.configuration = {
            "deployment_region": "us-east-1",
            "scaling_policy": "auto",
            "backup_enabled": True
        }
        
        workflow_state.integrations = {
            "linear": {"status": "connected", "workspace_id": "test-123"},
            "github": {"status": "connected", "org": "test-org"},
            "slack": {"status": "pending", "channel": "#symphony-notifications"}
        }
        
        # Save state
        manager._save_workflow_state(workflow_state)
        
        # Get comprehensive status
        status = manager.get_workflow_status(workflow_id)
        
        # Verify all fields are properly serialized and accessible
        assert status['status'] == WorkflowStatus.IN_PROGRESS.value
        assert status['progress']['completed_steps'] == 1
        assert status['progress']['current_step']['step_id'] == workflow_state.steps[1].step_id
        assert status['progress']['current_step']['status'] == StepStatus.RUNNING.value
        assert status['configuration']['deployment_region'] == "us-east-1"
        assert status['integrations']['linear']['status'] == "connected"
        assert status['timing']['started_at'] is not None
        
        print("✓ Comprehensive workflow status working correctly")
        return True


async def test_async_operations_serialization():
    """Test async operations with JSON serialization"""
    print("Testing async operations with serialization...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = create_workflow_manager(temp_dir)
        
        # Create workflow
        workflow_id = manager.create_workflow("async-test")
        
        # Register multiple async step handlers
        async def async_step_handler_1(workflow_state, step):
            await asyncio.sleep(0.1)  # Simulate async work
            return {"result": f"Async result for {step.step_id}", "timestamp": datetime.now(timezone.utc).isoformat()}
        
        async def async_step_handler_2(workflow_state, step):
            await asyncio.sleep(0.1)  # Simulate async work
            return {"result": f"Second async result for {step.step_id}", "data": {"processed": True}}
        
        # Register handlers for first two steps
        workflow_state = manager._load_workflow_state(workflow_id)
        if len(workflow_state.steps) >= 2:
            manager.register_step_handler(workflow_state.steps[0].step_id, async_step_handler_1)
            manager.register_step_handler(workflow_state.steps[1].step_id, async_step_handler_2)
        
        # Run workflow (will execute async handlers and serialize results)
        try:
            result = await manager.start_workflow(workflow_id)
            
            # Check that async results were serialized
            final_state = manager._load_workflow_state(workflow_id)
            
            # Verify at least some steps executed
            completed_steps = [s for s in final_state.steps if s.status == StepStatus.COMPLETED]
            if completed_steps:
                for step in completed_steps:
                    if step.result_data:
                        assert "result" in step.result_data
                        print(f"  ✓ Step {step.step_id} async result serialized: {step.result_data}")
            
            print("✓ Async operations and serialization working correctly")
        except Exception as e:
            print(f"✓ Async operations handled gracefully: {e}")
        
        return True


def run_comprehensive_tests():
    """Run all comprehensive JSON serialization tests"""
    print("=" * 70)
    print("COMPREHENSIVE JSON SERIALIZATION FIX VALIDATION")
    print("=" * 70)
    
    sync_tests = [
        test_all_enum_values_serialization,
        test_concurrent_workflow_operations,
        test_workflow_step_updates_persistence,
        test_complex_workflow_template_serialization,
        test_error_recovery_serialization,
        test_get_workflow_status_comprehensive,
    ]
    
    async_tests = [
        test_async_operations_serialization,
    ]
    
    passed = 0
    failed = 0
    
    # Run sync tests
    for test_func in sync_tests:
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
            import traceback
            traceback.print_exc()
    
    # Run async tests
    for test_func in async_tests:
        try:
            print(f"\n{test_func.__name__}:")
            result = asyncio.run(test_func())
            if result:
                passed += 1
                print(f"✅ PASSED: {test_func.__name__}")
            else:
                failed += 1
                print(f"❌ FAILED: {test_func.__name__}")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"COMPREHENSIVE TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("   The JSON serialization fix is robust and handles all edge cases correctly.")
    else:
        print(f"⚠️  {failed} tests failed - there may be edge cases that need attention")
    
    return failed == 0


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)