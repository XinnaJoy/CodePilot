#!/usr/bin/env python3
"""Facade for tool schemas and handlers."""
#工具注册中心，统一管理工具定义和处理器

from tool_handlers import build_system_prompt, build_tool_handlers
from tool_schemas import build_tools


class ToolRegistry:
    def __init__(self, get_context, shutdown_requests: dict, plan_requests: dict):
        self.get_context = get_context
        self.shutdown_requests = shutdown_requests
        self.plan_requests = plan_requests
        self._tools = build_tools()
        self._handlers = build_tool_handlers(get_context, shutdown_requests, plan_requests)

    @property
    def tools(self) -> list[dict]:
        return self._tools

    @property
    def handlers(self) -> dict:
        return self._handlers

    def system_prompt(self, config) -> str:
        return build_system_prompt(config, self.get_context())
