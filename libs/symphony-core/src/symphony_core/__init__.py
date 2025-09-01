"""
Symphony Core - Agent coordination and orchestration engine

This package provides the core functionality for Symphony's autonomous enterprise platform,
including agent definitions, coordination patterns, and core business logic.
"""

__version__ = "0.1.0"
__author__ = "Symphony Team"
__email__ = "team@symphony.ai"

from .agents import *
from .coordination import *
from .processors import *
from .utils import *

__all__ = [
    # Core modules will be imported here as they're migrated
]
