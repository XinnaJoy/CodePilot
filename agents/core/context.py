#!/usr/bin/env python3
"""Shared runtime context for the agent."""

from dataclasses import dataclass


@dataclass
class AgentContext:
    session_id: str
    config: object
    client: object
    file_store: object
    shell_runner: object
    todo: object
    skills: object
    tasks: object
    background: object
    bus: object
    memory: object
    team: object
    working_memory: object
    session_db: object
