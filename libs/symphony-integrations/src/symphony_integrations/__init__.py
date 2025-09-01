"""
Symphony Integrations - External tool integrations

This package provides integrations with external tools like Linear, GitHub, Slack,
and other services that Symphony coordinates with.
"""

__version__ = "0.1.0"
__author__ = "Symphony Team"
__email__ = "team@symphony.ai"

from .linear import *
from .github import *
from .common import *

__all__ = [
    # Integration modules will be imported here as they're migrated
]
