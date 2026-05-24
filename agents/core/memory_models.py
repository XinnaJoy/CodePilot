#!/usr/bin/env python3
"""Core in-memory models for the memory subsystem."""


class WorkingMemory:
    """Temporary in-memory state for the current task."""

    def __init__(self):
        self.context = {}
        self.goals = []

    def set(self, key: str, value: str) -> str:
        """Set working memory variable."""
        self.context[key] = value
        return f"Set {key} = {value[:100]}"

    def get(self, key: str) -> str:
        """Get working memory variable."""
        if key in self.context:
            return self.context[key]
        return f"Key '{key}' not found"

    def push_goal(self, goal: str) -> str:
        """Push sub-goal onto stack."""
        self.goals.append(goal)
        return f"Goal stack: {' > '.join(self.goals)}"

    def pop_goal(self) -> str:
        """Complete current goal and pop from stack."""
        if not self.goals:
            return "No goals in stack"

        completed = self.goals.pop()
        remaining = f"\nRemaining: {self.goals}" if self.goals else ""
        return f"Completed: {completed}{remaining}"

    def render(self) -> str:
        """Render current working memory state."""
        if not self.goals and not self.context:
            return "Empty"

        lines = ["=== Working Memory ==="]

        if self.goals:
            lines.append(f"Goals: {' > '.join(self.goals)}")

        if self.context:
            lines.append("Context:")
            for key, value in self.context.items():
                lines.append(f"  {key}: {str(value)[:80]}")

        return "\n".join(lines)

    def clear(self):
        """Clear all working memory."""
        self.context.clear()
        self.goals.clear()

    def to_dict(self) -> dict:
        """Export working memory state."""
        return {
            "context": self.context.copy(),
            "goals": self.goals.copy(),
        }

    def from_dict(self, data: dict):
        """Import working memory state."""
        self.context = data.get("context", {})
        self.goals = data.get("goals", [])
