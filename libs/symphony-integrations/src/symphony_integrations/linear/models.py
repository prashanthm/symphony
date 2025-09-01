#!/usr/bin/env python3
"""
Linear API Data Models

Data classes for Linear API entities used throughout Symphony integrations.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LinearTeam:
    id: str
    name: str
    key: str


@dataclass 
class LinearProject:
    id: str
    name: str
    description: str
    team_id: str
    url: str


@dataclass
class LinearIssue:
    id: str
    title: str
    description: str
    project_id: Optional[str]
    assignee_id: Optional[str]
    state_id: str
    priority: int
    url: str


@dataclass
class LinearWorkflow:
    id: str
    name: str
    type: str
    team_id: str