#!/usr/bin/env python3
"""
Base Agent Framework for Symphony Autonomous Enterprise

Provides the foundation for all Symphony agents with common functionality
for coordination, scheduling, performance tracking, and handoffs.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent operational status"""
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class HandoffStatus(Enum):
    """Handoff operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentCapability:
    """Represents a specific agent capability"""
    name: str
    description: str
    priority: str  # critical, high, medium, low
    enabled: bool = True
    performance_target: Optional[float] = None


@dataclass
class AgentSchedule:
    """Agent operational schedule"""
    morning_start: str = "6:00 AM EST"
    midday_optimization: str = "12:00 PM EST"
    evening_planning: str = "6:00 PM EST"
    timezone: str = "EST"
    enabled: bool = True
    custom_schedules: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class HandoffContext:
    """Context package for agent handoffs"""
    handoff_id: str
    from_agent: str
    to_agent: str
    user_objective: str
    completion_summary: str
    key_findings: List[str]
    next_actions: List[str]
    context_data: Dict[str, Any]
    timestamp: str
    token_count: int
    status: HandoffStatus = HandoffStatus.PENDING


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time: float = 0.0
    success_rate: float = 0.0
    handoff_success_rate: float = 0.0
    last_activity: Optional[str] = None
    uptime: float = 0.0


class BaseAgent(ABC):
    """Base class for all Symphony agents"""
    
    def __init__(self, 
                 agent_id: str,
                 name: str,
                 role: str,
                 category: str,
                 capabilities: List[AgentCapability],
                 schedule: AgentSchedule = None,
                 customer_id: Optional[str] = None):
        
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.category = category  # coordination, leadership, specialists, maestro
        self.capabilities = capabilities
        self.schedule = schedule or AgentSchedule()
        self.customer_id = customer_id
        
        # Operational state
        self.status = AgentStatus.INACTIVE
        self.metrics = AgentMetrics()
        self.context_memory: List[HandoffContext] = []
        self.active_tasks: Dict[str, Any] = {}
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            'task_started': [],
            'task_completed': [],
            'task_failed': [],
            'handoff_received': [],
            'handoff_sent': [],
            'error_occurred': []
        }
        
        # Configuration
        self.max_context_memory = 100
        self.max_token_context = 500
        self.performance_targets = {
            'success_rate': 99.5,
            'response_time': 5.0,
            'handoff_success': 99.0
        }
        
        logger.info(f"Agent {self.name} ({self.agent_id}) initialized")
    
    async def initialize(self) -> bool:
        """Initialize the agent and prepare for operations"""
        try:
            self.status = AgentStatus.INITIALIZING
            
            # Perform agent-specific initialization
            await self._initialize_agent()
            
            # Validate capabilities
            if not await self._validate_capabilities():
                raise Exception("Capability validation failed")
            
            # Setup schedules
            await self._setup_schedules()
            
            # Load any persisted state
            await self._load_agent_state()
            
            self.status = AgentStatus.ACTIVE
            self._emit_event('agent_initialized', {'agent_id': self.agent_id})
            
            logger.info(f"Agent {self.name} successfully initialized")
            return True
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Agent {self.name} initialization failed: {e}")
            self._emit_event('error_occurred', {'error': str(e), 'phase': 'initialization'})
            return False
    
    async def shutdown(self) -> bool:
        """Gracefully shutdown the agent"""
        try:
            logger.info(f"Shutting down agent {self.name}")
            
            # Complete any active tasks
            await self._complete_active_tasks()
            
            # Save agent state
            await self._save_agent_state()
            
            # Perform agent-specific cleanup
            await self._cleanup_agent()
            
            self.status = AgentStatus.INACTIVE
            self._emit_event('agent_shutdown', {'agent_id': self.agent_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Agent {self.name} shutdown failed: {e}")
            self._emit_event('error_occurred', {'error': str(e), 'phase': 'shutdown'})
            return False
    
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with the agent"""
        task_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        try:
            self.status = AgentStatus.BUSY
            self.active_tasks[task_id] = {
                'task_data': task_data,
                'start_time': start_time,
                'status': 'running'
            }
            
            self._emit_event('task_started', {'task_id': task_id, 'task_data': task_data})
            
            # Execute the task
            result = await self._execute_task_impl(task_data)
            
            # Update metrics
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._update_task_metrics(True, execution_time)
            
            # Clean up active task
            del self.active_tasks[task_id]
            self.status = AgentStatus.ACTIVE
            
            self._emit_event('task_completed', {
                'task_id': task_id,
                'result': result,
                'execution_time': execution_time
            })
            
            return {
                'success': True,
                'result': result,
                'task_id': task_id,
                'execution_time': execution_time
            }
            
        except Exception as e:
            # Update error metrics
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._update_task_metrics(False, execution_time)
            
            # Clean up and reset status
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            self.status = AgentStatus.ACTIVE
            
            self._emit_event('task_failed', {
                'task_id': task_id,
                'error': str(e),
                'execution_time': execution_time
            })
            
            logger.error(f"Task execution failed for agent {self.name}: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'task_id': task_id,
                'execution_time': execution_time
            }
    
    async def handle_handoff(self, handoff_context: HandoffContext) -> bool:
        """Handle incoming handoff from another agent"""
        try:
            logger.info(f"Agent {self.name} receiving handoff from {handoff_context.from_agent}")
            
            # Validate handoff context
            if not self._validate_handoff_context(handoff_context):
                raise Exception("Invalid handoff context")
            
            # Store context in memory
            self._store_handoff_context(handoff_context)
            
            # Process the handoff
            success = await self._process_handoff(handoff_context)
            
            if success:
                handoff_context.status = HandoffStatus.COMPLETED
                self._emit_event('handoff_received', {
                    'handoff_id': handoff_context.handoff_id,
                    'from_agent': handoff_context.from_agent
                })
            else:
                handoff_context.status = HandoffStatus.FAILED
                
            return success
            
        except Exception as e:
            handoff_context.status = HandoffStatus.FAILED
            logger.error(f"Handoff processing failed for agent {self.name}: {e}")
            self._emit_event('error_occurred', {'error': str(e), 'phase': 'handoff'})
            return False
    
    async def initiate_handoff(self, to_agent: str, context_data: Dict[str, Any]) -> HandoffContext:
        """Initiate handoff to another agent"""
        handoff_context = HandoffContext(
            handoff_id=str(uuid.uuid4()),
            from_agent=self.agent_id,
            to_agent=to_agent,
            user_objective=context_data.get('user_objective', ''),
            completion_summary=context_data.get('completion_summary', ''),
            key_findings=context_data.get('key_findings', []),
            next_actions=context_data.get('next_actions', []),
            context_data=context_data,
            timestamp=datetime.now(timezone.utc).isoformat(),
            token_count=self._calculate_token_count(context_data),
            status=HandoffStatus.PENDING
        )
        
        # Validate token limit
        if handoff_context.token_count > self.max_token_context:
            logger.warning(f"Handoff context exceeds token limit: {handoff_context.token_count}")
            # Implement context compression if needed
        
        self._emit_event('handoff_sent', {
            'handoff_id': handoff_context.handoff_id,
            'to_agent': to_agent
        })
        
        logger.info(f"Agent {self.name} initiated handoff to {to_agent}")
        return handoff_context
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'role': self.role,
            'category': self.category,
            'status': self.status.value,
            'capabilities': [cap.name for cap in self.capabilities if cap.enabled],
            'metrics': {
                'total_tasks': self.metrics.total_tasks,
                'completed_tasks': self.metrics.completed_tasks,
                'success_rate': self.metrics.success_rate,
                'avg_response_time': self.metrics.avg_response_time,
                'handoff_success_rate': self.metrics.handoff_success_rate,
                'last_activity': self.metrics.last_activity,
                'uptime': self.metrics.uptime
            },
            'active_tasks': len(self.active_tasks),
            'context_memory_size': len(self.context_memory),
            'performance_targets': self.performance_targets
        }
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add event handler for agent events"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    # Abstract methods that must be implemented by specific agents
    
    @abstractmethod
    async def _initialize_agent(self) -> None:
        """Agent-specific initialization logic"""
        pass
    
    @abstractmethod
    async def _execute_task_impl(self, task_data: Dict[str, Any]) -> Any:
        """Agent-specific task execution logic"""
        pass
    
    @abstractmethod
    async def _process_handoff(self, handoff_context: HandoffContext) -> bool:
        """Agent-specific handoff processing logic"""
        pass
    
    # Internal helper methods
    
    async def _validate_capabilities(self) -> bool:
        """Validate agent capabilities"""
        for capability in self.capabilities:
            if capability.enabled and not await self._test_capability(capability):
                logger.error(f"Capability validation failed: {capability.name}")
                return False
        return True
    
    async def _test_capability(self, capability: AgentCapability) -> bool:
        """Test a specific capability - override in derived classes"""
        return True
    
    async def _setup_schedules(self) -> None:
        """Setup agent schedules"""
        if self.schedule.enabled:
            # In a full implementation, this would setup actual scheduling
            logger.info(f"Schedule setup for {self.name}: {self.schedule}")
    
    async def _load_agent_state(self) -> None:
        """Load persisted agent state"""
        # Implementation would load from disk/database
        pass
    
    async def _save_agent_state(self) -> None:
        """Save agent state to disk"""
        # Implementation would save to disk/database
        pass
    
    async def _complete_active_tasks(self) -> None:
        """Complete or gracefully cancel active tasks"""
        for task_id, task_info in list(self.active_tasks.items()):
            logger.info(f"Cancelling active task {task_id} for agent {self.name}")
            # Implementation would handle graceful task cancellation
    
    async def _cleanup_agent(self) -> None:
        """Agent-specific cleanup logic"""
        pass
    
    def _validate_handoff_context(self, context: HandoffContext) -> bool:
        """Validate handoff context"""
        required_fields = ['user_objective', 'completion_summary']
        for field in required_fields:
            if not getattr(context, field):
                logger.error(f"Missing required handoff field: {field}")
                return False
        return True
    
    def _store_handoff_context(self, context: HandoffContext) -> None:
        """Store handoff context in agent memory"""
        self.context_memory.append(context)
        
        # Maintain memory limit
        if len(self.context_memory) > self.max_context_memory:
            self.context_memory.pop(0)
    
    def _calculate_token_count(self, context_data: Dict[str, Any]) -> int:
        """Calculate approximate token count for context"""
        # Simplified token calculation - in production use proper tokenizer
        context_str = json.dumps(context_data)
        return len(context_str.split())
    
    def _update_task_metrics(self, success: bool, execution_time: float) -> None:
        """Update agent performance metrics"""
        self.metrics.total_tasks += 1
        if success:
            self.metrics.completed_tasks += 1
        else:
            self.metrics.failed_tasks += 1
        
        # Update success rate
        self.metrics.success_rate = (
            self.metrics.completed_tasks / self.metrics.total_tasks * 100
        )
        
        # Update average response time
        if self.metrics.avg_response_time == 0:
            self.metrics.avg_response_time = execution_time
        else:
            self.metrics.avg_response_time = (
                (self.metrics.avg_response_time + execution_time) / 2
            )
        
        self.metrics.last_activity = datetime.now(timezone.utc).isoformat()
    
    def _emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Emit agent event to registered handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(event_data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")


# Utility functions for agent management

def create_agent_capability(name: str, description: str, priority: str = "medium") -> AgentCapability:
    """Create an agent capability"""
    return AgentCapability(
        name=name,
        description=description,
        priority=priority
    )


def create_agent_schedule(
    morning: str = "6:00 AM EST",
    midday: str = "12:00 PM EST", 
    evening: str = "6:00 PM EST"
) -> AgentSchedule:
    """Create an agent schedule"""
    return AgentSchedule(
        morning_start=morning,
        midday_optimization=midday,
        evening_planning=evening
    )