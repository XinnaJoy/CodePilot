#!/usr/bin/env python3
"""
Memory System for MyAgent - Minimal version

Core features:
1. Working Memory: In-memory temporary state for current task
2. Session Recovery: Save/restore conversation context after compression
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import List, Dict, Optional


class WorkingMemory:
    """Working Memory: Temporary in-memory state for current task"""
    
    def __init__(self):
        self.context = {}
        self.goals = []
    
    def set(self, key: str, value: str) -> str:
        """Set working memory variable"""
        self.context[key] = value
        return f"Set {key} = {value[:100]}"
    
    def get(self, key: str) -> str:
        """Get working memory variable"""
        if key in self.context:
            return self.context[key]
        return f"Key '{key}' not found"
    
    def push_goal(self, goal: str) -> str:
        """Push sub-goal onto stack"""
        self.goals.append(goal)
        return f"Goal stack: {' > '.join(self.goals)}"
    
    def pop_goal(self) -> str:
        """Complete current goal and pop from stack"""
        if not self.goals:
            return "No goals in stack"
        
        completed = self.goals.pop()
        remaining = f"\nRemaining: {self.goals}" if self.goals else ""
        return f"Completed: {completed}{remaining}"
    
    def render(self) -> str:
        """Render current working memory state"""
        if not self.goals and not self.context:
            return "Empty"
        
        lines = ["=== Working Memory ==="]
        
        if self.goals:
            lines.append(f"Goals: {' > '.join(self.goals)}")
        
        if self.context:
            lines.append("Context:")
            for k, v in self.context.items():
                lines.append(f"  {k}: {str(v)[:80]}")
        
        return "\n".join(lines)
    
    def clear(self):
        """Clear all working memory"""
        self.context.clear()
        self.goals.clear()
    
    def to_dict(self) -> dict:
        """Export working memory state"""
        return {
            "context": self.context.copy(),
            "goals": self.goals.copy()
        }
    
    def from_dict(self, data: dict):
        """Import working memory state"""
        self.context = data.get("context", {})
        self.goals = data.get("goals", [])


class SessionDB:
    """Session Recovery: Save/restore conversation snapshots"""
    
    def __init__(self, db_path: Path):
        """Initialize database connection and schema"""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(
            str(db_path),
            check_same_thread=False,
            timeout=10.0
        )
        self.conn.row_factory = sqlite3.Row
        
        self._init_schema()
    
    def _init_schema(self):
        """Create session snapshots table"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                snapshot_type TEXT NOT NULL,
                messages TEXT NOT NULL,
                working_memory TEXT,
                created_at REAL NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON session_snapshots(session_id, created_at DESC)
        """)
        
        self.conn.commit()
    
    def save_snapshot(
        self,
        session_id: str,
        messages: List[Dict],
        working_memory: Optional[Dict] = None,
        snapshot_type: str = "auto_compact"
    ) -> int:
        """Save conversation snapshot before compression"""
        cursor = self.conn.cursor()
        now = time.time()
        
        messages_json = json.dumps(messages, default=str)
        wm_json = json.dumps(working_memory) if working_memory else None
        
        cursor.execute("""
            INSERT INTO session_snapshots 
            (session_id, snapshot_type, messages, working_memory, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, snapshot_type, messages_json, wm_json, now))
        
        snapshot_id = cursor.lastrowid
        self.conn.commit()
        
        return snapshot_id
    
    def get_latest_snapshot(self, session_id: str) -> Optional[Dict]:
        """Get the most recent snapshot for a session"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM session_snapshots
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (session_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "snapshot_type": row["snapshot_type"],
            "messages": json.loads(row["messages"]),
            "working_memory": json.loads(row["working_memory"]) if row["working_memory"] else None,
            "created_at": row["created_at"]
        }
    
    def list_snapshots(self, session_id: str, limit: int = 10) -> List[Dict]:
        """List recent snapshots for a session"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, session_id, snapshot_type, created_at,
                   length(messages) as size_bytes
            FROM session_snapshots
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (session_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def list_all_snapshots(self, limit: int = 10) -> List[Dict]:
        """List all snapshots across all sessions"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, session_id, snapshot_type, created_at,
                   length(messages) as size_bytes
            FROM session_snapshots
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_snapshots(self, session_id: str, keep_last: int = 5):
        """Keep only the N most recent snapshots"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            DELETE FROM session_snapshots
            WHERE session_id = ?
            AND id NOT IN (
                SELECT id FROM session_snapshots
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            )
        """, (session_id, session_id, keep_last))
        
        deleted = cursor.rowcount
        self.conn.commit()
        
        return deleted
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM session_snapshots")
        total_snapshots = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(DISTINCT session_id) as count FROM session_snapshots")
        unique_sessions = cursor.fetchone()['count']
        
        db_size_kb = self.db_path.stat().st_size // 1024 if self.db_path.exists() else 0
        
        return {
            "total_snapshots": total_snapshots,
            "unique_sessions": unique_sessions,
            "db_size_kb": db_size_kb
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()


def create_memory_system(workdir: Path) -> tuple:
    """
    Create minimal memory system
    
    Returns:
        (WorkingMemory, SessionDB) tuple
    """
    memory_dir = workdir / ".memory"
    memory_dir.mkdir(exist_ok=True)
    
    working_mem = WorkingMemory()
    session_db = SessionDB(memory_dir / "sessions.db")
    
    return working_mem, session_db
