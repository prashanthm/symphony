#!/usr/bin/env python3
"""
Integration Orchestration Framework

Provides centralized coordination for all Symphony integrations including
Linear, GitHub, Slack, HubSpot, and other enterprise tools.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """Integration operational status"""
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    SYNCING = "syncing"


class OrchestrationType(Enum):
    """Types of orchestration patterns"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    EVENT_DRIVEN = "event_driven"
    WORKFLOW = "workflow"


@dataclass
class IntegrationEvent:
    """Event data structure for integration coordination"""
    event_id: str
    integration_name: str
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    priority: str = "medium"  # low, medium, high, critical
    correlation_id: Optional[str] = None


@dataclass
class OrchestrationRule:
    """Rule for coordinating integration behavior"""
    rule_id: str
    name: str
    trigger_conditions: List[str]
    target_integrations: List[str]
    orchestration_type: OrchestrationType
    actions: List[Dict[str, Any]]
    enabled: bool = True


@dataclass
class IntegrationHealth:
    """Health status for an integration"""
    integration_name: str
    status: IntegrationStatus
    last_sync: Optional[str] = None
    error_count: int = 0
    success_rate: float = 100.0
    response_time_avg: float = 0.0
    last_error: Optional[str] = None


class BaseIntegrationAdapter(ABC):
    """Base class for all integration adapters"""
    
    def __init__(self, integration_name: str, config: Dict[str, Any]):
        self.integration_name = integration_name
        self.config = config
        self.status = IntegrationStatus.INACTIVE
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.health = IntegrationHealth(integration_name, IntegrationStatus.INACTIVE)
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the integration"""
        pass
    
    @abstractmethod
    async def sync_data(self, data_type: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Sync data with the integration"""
        pass
    
    @abstractmethod
    async def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action on the integration"""
        pass
    
    @abstractmethod
    async def get_health_status(self) -> IntegrationHealth:
        """Get current health status"""
        pass
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add event handler for integration events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def emit_event(self, event: IntegrationEvent):
        """Emit integration event to registered handlers"""
        event_type = event.event_type
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler error for {self.integration_name}: {e}")


class IntegrationOrchestrator:
    """Central coordinator for all Symphony integrations"""
    
    def __init__(self):
        self.integrations: Dict[str, BaseIntegrationAdapter] = {}
        self.orchestration_rules: List[OrchestrationRule] = []
        self.event_queue: List[IntegrationEvent] = []
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.metrics = {
            'total_events': 0,
            'successful_orchestrations': 0,
            'failed_orchestrations': 0,
            'active_integrations': 0
        }
        
        # Event processing loop
        self._processing_events = False
        
        logger.info("Integration Orchestrator initialized")
    
    async def register_integration(self, adapter: BaseIntegrationAdapter) -> bool:
        """Register an integration adapter"""
        try:
            self.integrations[adapter.integration_name] = adapter
            
            # Add default event handlers for orchestration
            adapter.add_event_handler("data_sync", self._handle_data_sync_event)
            adapter.add_event_handler("error", self._handle_error_event)
            adapter.add_event_handler("status_change", self._handle_status_change_event)
            
            # Initialize the integration
            if await adapter.initialize():
                self.metrics['active_integrations'] += 1
                logger.info(f"Integration {adapter.integration_name} registered successfully")
                return True
            else:
                logger.error(f"Failed to initialize integration {adapter.integration_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering integration {adapter.integration_name}: {e}")
            return False
    
    async def add_orchestration_rule(self, rule: OrchestrationRule):
        """Add orchestration rule"""
        self.orchestration_rules.append(rule)
        logger.info(f"Orchestration rule '{rule.name}' added")
    
    async def trigger_orchestration(self, trigger_event: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger orchestration based on event"""
        logger.info(f"Triggering orchestration for event: {trigger_event}")
        
        # Find matching rules
        matching_rules = [
            rule for rule in self.orchestration_rules 
            if rule.enabled and trigger_event in rule.trigger_conditions
        ]
        
        results = []
        
        for rule in matching_rules:
            try:
                result = await self._execute_orchestration_rule(rule, context or {})
                results.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'success': result['success'],
                    'details': result.get('details', [])
                })
                
                if result['success']:
                    self.metrics['successful_orchestrations'] += 1
                else:
                    self.metrics['failed_orchestrations'] += 1
                    
            except Exception as e:
                logger.error(f"Error executing orchestration rule {rule.name}: {e}")
                results.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'success': False,
                    'error': str(e)
                })
                self.metrics['failed_orchestrations'] += 1
        
        return {
            'trigger_event': trigger_event,
            'rules_executed': len(results),
            'results': results
        }
    
    async def sync_all_integrations(self, data_type: str = "all") -> Dict[str, Any]:
        """Sync data across all active integrations"""
        logger.info(f"Starting sync across all integrations for data type: {data_type}")
        
        sync_results = {}
        
        for integration_name, adapter in self.integrations.items():
            if adapter.status == IntegrationStatus.ACTIVE:
                try:
                    result = await adapter.sync_data(data_type)
                    sync_results[integration_name] = {
                        'success': True,
                        'result': result
                    }
                except Exception as e:
                    logger.error(f"Sync failed for {integration_name}: {e}")
                    sync_results[integration_name] = {
                        'success': False,
                        'error': str(e)
                    }
            else:
                sync_results[integration_name] = {
                    'success': False,
                    'error': f"Integration not active (status: {adapter.status})"
                }
        
        return {
            'data_type': data_type,
            'integrations_synced': len(sync_results),
            'results': sync_results
        }
    
    async def get_orchestration_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestration status"""
        integration_status = {}
        
        for integration_name, adapter in self.integrations.items():
            health = await adapter.get_health_status()
            integration_status[integration_name] = {
                'status': health.status.value,
                'last_sync': health.last_sync,
                'success_rate': health.success_rate,
                'response_time_avg': health.response_time_avg,
                'error_count': health.error_count,
                'last_error': health.last_error
            }
        
        return {
            'orchestrator_metrics': self.metrics,
            'integration_status': integration_status,
            'orchestration_rules': len(self.orchestration_rules),
            'active_workflows': len(self.active_workflows),
            'event_queue_size': len(self.event_queue),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def execute_workflow(self, workflow_name: str, steps: List[Dict[str, Any]], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a multi-step integration workflow"""
        workflow_id = str(uuid.uuid4())
        
        self.active_workflows[workflow_id] = {
            'name': workflow_name,
            'steps': steps,
            'context': context or {},
            'current_step': 0,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'status': 'running'
        }
        
        logger.info(f"Starting workflow '{workflow_name}' with ID: {workflow_id}")
        
        try:
            results = []
            
            for i, step in enumerate(steps):
                self.active_workflows[workflow_id]['current_step'] = i
                
                integration_name = step.get('integration')
                action = step.get('action')
                params = step.get('params', {})
                
                if integration_name not in self.integrations:
                    raise Exception(f"Integration '{integration_name}' not found")
                
                adapter = self.integrations[integration_name]
                result = await adapter.execute_action(action, params)
                
                results.append({
                    'step': i,
                    'integration': integration_name,
                    'action': action,
                    'success': result.get('success', True),
                    'result': result
                })
                
                # Handle step dependencies or conditions
                if not result.get('success', True) and step.get('required', True):
                    self.active_workflows[workflow_id]['status'] = 'failed'
                    raise Exception(f"Required step {i} failed: {result.get('error', 'Unknown error')}")
            
            self.active_workflows[workflow_id]['status'] = 'completed'
            logger.info(f"Workflow '{workflow_name}' completed successfully")
            
            return {
                'workflow_id': workflow_id,
                'workflow_name': workflow_name,
                'success': True,
                'steps_completed': len(results),
                'results': results
            }
            
        except Exception as e:
            self.active_workflows[workflow_id]['status'] = 'failed'
            self.active_workflows[workflow_id]['error'] = str(e)
            logger.error(f"Workflow '{workflow_name}' failed: {e}")
            
            return {
                'workflow_id': workflow_id,
                'workflow_name': workflow_name,
                'success': False,
                'error': str(e),
                'results': results if 'results' in locals() else []
            }
        finally:
            # Clean up completed/failed workflows after some time
            # This would be handled by a cleanup task in production
            pass
    
    # Event handlers
    async def _handle_data_sync_event(self, event: IntegrationEvent):
        """Handle data sync events"""
        logger.info(f"Data sync event from {event.integration_name}: {event.event_type}")
        # Trigger any orchestration rules for data sync events
        await self.trigger_orchestration("data_sync", event.data)
    
    async def _handle_error_event(self, event: IntegrationEvent):
        """Handle error events"""
        logger.warning(f"Error event from {event.integration_name}: {event.data.get('error', 'Unknown error')}")
        # Implement error handling orchestration
        await self.trigger_orchestration("integration_error", event.data)
    
    async def _handle_status_change_event(self, event: IntegrationEvent):
        """Handle status change events"""
        logger.info(f"Status change event from {event.integration_name}: {event.data}")
        await self.trigger_orchestration("status_change", event.data)
    
    # Internal methods
    async def _execute_orchestration_rule(self, rule: OrchestrationRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific orchestration rule"""
        logger.info(f"Executing orchestration rule: {rule.name}")
        
        action_results = []
        
        if rule.orchestration_type == OrchestrationType.SEQUENTIAL:
            # Execute actions sequentially
            for action in rule.actions:
                result = await self._execute_action(action, rule.target_integrations, context)
                action_results.append(result)
                
        elif rule.orchestration_type == OrchestrationType.PARALLEL:
            # Execute actions in parallel
            tasks = [
                self._execute_action(action, rule.target_integrations, context)
                for action in rule.actions
            ]
            action_results = await asyncio.gather(*tasks, return_exceptions=True)
            
        elif rule.orchestration_type == OrchestrationType.CONDITIONAL:
            # Execute actions based on conditions
            for action in rule.actions:
                condition = action.get('condition')
                if condition and self._evaluate_condition(condition, context):
                    result = await self._execute_action(action, rule.target_integrations, context)
                    action_results.append(result)
                    
        elif rule.orchestration_type == OrchestrationType.EVENT_DRIVEN:
            # Handle event-driven orchestration
            for action in rule.actions:
                result = await self._execute_action(action, rule.target_integrations, context)
                action_results.append(result)
        
        success = all(result.get('success', False) for result in action_results if not isinstance(result, Exception))
        
        return {
            'success': success,
            'details': action_results
        }
    
    async def _execute_action(self, action: Dict[str, Any], target_integrations: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific action on target integrations"""
        action_type = action.get('type')
        action_params = action.get('params', {})
        
        # Merge context into action parameters
        merged_params = {**action_params, **context}
        
        results = {}
        
        for integration_name in target_integrations:
            if integration_name in self.integrations:
                adapter = self.integrations[integration_name]
                try:
                    result = await adapter.execute_action(action_type, merged_params)
                    results[integration_name] = result
                except Exception as e:
                    results[integration_name] = {'success': False, 'error': str(e)}
            else:
                results[integration_name] = {'success': False, 'error': 'Integration not found'}
        
        return {
            'action_type': action_type,
            'success': all(result.get('success', False) for result in results.values()),
            'results': results
        }
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition string against context"""
        # Simple condition evaluation - in production this would be more sophisticated
        try:
            # Replace context variables in condition
            for key, value in context.items():
                condition = condition.replace(f"${key}", str(value))
            
            # Evaluate the condition (this is simplified)
            return eval(condition)
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False


# Factory function
def create_integration_orchestrator() -> IntegrationOrchestrator:
    """Create and return an integration orchestrator instance"""
    return IntegrationOrchestrator()


# Utility functions for common orchestration patterns
async def create_data_sync_rule(integrations: List[str], sync_type: str = "bidirectional") -> OrchestrationRule:
    """Create a data synchronization orchestration rule"""
    return OrchestrationRule(
        rule_id=str(uuid.uuid4()),
        name=f"Data Sync Rule - {','.join(integrations)}",
        trigger_conditions=["data_change", "scheduled_sync"],
        target_integrations=integrations,
        orchestration_type=OrchestrationType.PARALLEL,
        actions=[
            {
                'type': 'sync_data',
                'params': {'sync_type': sync_type}
            }
        ]
    )


async def create_error_handling_rule(integrations: List[str]) -> OrchestrationRule:
    """Create an error handling orchestration rule"""
    return OrchestrationRule(
        rule_id=str(uuid.uuid4()),
        name=f"Error Handling Rule - {','.join(integrations)}",
        trigger_conditions=["integration_error", "sync_failure"],
        target_integrations=integrations,
        orchestration_type=OrchestrationType.CONDITIONAL,
        actions=[
            {
                'type': 'retry_operation',
                'condition': '$error_count < 3',
                'params': {'max_retries': 3}
            },
            {
                'type': 'escalate_error',
                'condition': '$error_count >= 3',
                'params': {'notification_channels': ['admin', 'ops_team']}
            }
        ]
    )