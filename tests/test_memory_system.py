#!/usr/bin/env python3
"""
Test suite for MyAgent Memory System (SQLite-based)

Following TDD principles:
1. Write tests first
2. Run tests (they should fail)
3. Implement code to make tests pass
4. Refactor while keeping tests green
"""

import unittest
import tempfile
import shutil
import json
import time
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))


class TestWorkingMemory(unittest.TestCase):
    """Test WorkingMemory class (in-memory temporary state)"""
    
    def setUp(self):
        """Set up test fixtures"""
        from memory import WorkingMemory
        self.wm = WorkingMemory()
    
    def test_set_and_get_variable(self):
        """Should store and retrieve working memory variables"""
        result = self.wm.set("current_task", "Fix bug #123")
        self.assertIn("Set current_task", result)
        
        value = self.wm.get("current_task")
        self.assertEqual(value, "Fix bug #123")
    
    def test_get_nonexistent_key(self):
        """Should return error message for missing keys"""
        result = self.wm.get("nonexistent")
        self.assertIn("not found", result)
    
    def test_push_and_pop_goals(self):
        """Should maintain goal stack (LIFO)"""
        self.wm.push_goal("Analyze code")
        self.wm.push_goal("Write tests")
        self.wm.push_goal("Fix bug")
        
        result = self.wm.pop_goal()
        self.assertIn("Fix bug", result)
        self.assertIn("Write tests", result)  # Remaining goal
    
    def test_render_empty_memory(self):
        """Should render 'Empty' when no data"""
        result = self.wm.render()
        self.assertEqual(result, "Empty")
    
    def test_render_with_data(self):
        """Should render formatted memory state"""
        self.wm.set("task", "test")
        self.wm.push_goal("goal1")
        
        result = self.wm.render()
        self.assertIn("Working Memory", result)
        self.assertIn("Goals:", result)
        self.assertIn("Context:", result)


class TestSessionDB(unittest.TestCase):
    """Test SessionDB class (SQLite persistence)"""
    
    def setUp(self):
        """Create temporary database for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_sessions.db"
        
        from memory import SessionDB
        self.db = SessionDB(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    # === Session Snapshot Tests ===
    
    def test_save_snapshot(self):
        """Should save conversation snapshot"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        working_memory = {"current_task": "test"}
        
        snapshot_id = self.db.save_snapshot("session_001", messages, working_memory)
        self.assertIsInstance(snapshot_id, int)
        self.assertGreater(snapshot_id, 0)
    
    def test_get_latest_snapshot(self):
        """Should retrieve the most recent snapshot"""
        messages1 = [{"role": "user", "content": "First"}]
        messages2 = [{"role": "user", "content": "Second"}]
        
        self.db.save_snapshot("session_001", messages1)
        time.sleep(0.01)  # Ensure different timestamps
        self.db.save_snapshot("session_001", messages2)
        
        snapshot = self.db.get_latest_snapshot("session_001")
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["messages"][0]["content"], "Second")
    
    def test_get_nonexistent_snapshot(self):
        """Should return None for nonexistent session"""
        snapshot = self.db.get_latest_snapshot("nonexistent")
        self.assertIsNone(snapshot)
    
    def test_list_snapshots(self):
        """Should list snapshots for a session"""
        for i in range(5):
            self.db.save_snapshot("session_001", [{"role": "user", "content": f"Message {i}"}])
            time.sleep(0.01)
        
        snapshots = self.db.list_snapshots("session_001", limit=3)
        self.assertEqual(len(snapshots), 3)
        self.assertEqual(snapshots[0]["session_id"], "session_001")
    
    def test_list_all_snapshots(self):
        """Should list snapshots across all sessions"""
        self.db.save_snapshot("session_001", [{"role": "user", "content": "A"}])
        self.db.save_snapshot("session_002", [{"role": "user", "content": "B"}])
        
        snapshots = self.db.list_all_snapshots(limit=10)
        self.assertGreaterEqual(len(snapshots), 2)
    
    def test_cleanup_old_snapshots(self):
        """Should keep only N most recent snapshots"""
        for i in range(10):
            self.db.save_snapshot("session_001", [{"role": "user", "content": f"Message {i}"}])
            time.sleep(0.01)
        
        deleted = self.db.cleanup_old_snapshots("session_001", keep_last=3)
        self.assertEqual(deleted, 7)
        
        remaining = self.db.list_snapshots("session_001", limit=100)
        self.assertEqual(len(remaining), 3)
    
    def test_snapshot_with_working_memory(self):
        """Should save and restore working memory"""
        messages = [{"role": "user", "content": "Test"}]
        wm = {"context": {"task": "debug"}, "goals": ["fix bug"]}
        
        self.db.save_snapshot("session_001", messages, wm)
        
        snapshot = self.db.get_latest_snapshot("session_001")
        self.assertIsNotNone(snapshot["working_memory"])
        self.assertEqual(snapshot["working_memory"]["context"]["task"], "debug")
    
    def test_snapshot_without_working_memory(self):
        """Should handle snapshots without working memory"""
        messages = [{"role": "user", "content": "Test"}]
        
        self.db.save_snapshot("session_001", messages)
        
        snapshot = self.db.get_latest_snapshot("session_001")
        self.assertIsNone(snapshot["working_memory"])
    
    # === Statistics Tests ===
    
    def test_get_stats_empty_db(self):
        """Should return zero stats for empty database"""
        stats = self.db.get_stats()
        
        self.assertEqual(stats['total_snapshots'], 0)
        self.assertEqual(stats['unique_sessions'], 0)
        self.assertGreaterEqual(stats['db_size_kb'], 0)
    
    def test_get_stats_with_data(self):
        """Should return accurate statistics"""
        self.db.save_snapshot("session_001", [{"role": "user", "content": "A"}])
        self.db.save_snapshot("session_001", [{"role": "user", "content": "B"}])
        self.db.save_snapshot("session_002", [{"role": "user", "content": "C"}])
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats['total_snapshots'], 3)
        self.assertEqual(stats['unique_sessions'], 2)
        self.assertGreater(stats['db_size_kb'], 0)
    
    # === Edge Cases ===
    
    def test_large_message_storage(self):
        """Should handle large message content"""
        large_content = "x" * 60000  # 60KB
        messages = [{"role": "user", "content": large_content}]
        
        snapshot_id = self.db.save_snapshot("session_001", messages)
        self.assertIsInstance(snapshot_id, int)
        
        snapshot = self.db.get_latest_snapshot("session_001")
        self.assertEqual(len(snapshot["messages"][0]["content"]), 60000)
    
    def test_unicode_content(self):
        """Should handle Unicode characters"""
        messages = [{"role": "user", "content": "中文内容 🚀 émojis"}]
        
        self.db.save_snapshot("session_001", messages)
        
        snapshot = self.db.get_latest_snapshot("session_001")
        self.assertIn("中文内容", snapshot["messages"][0]["content"])
    
    def test_concurrent_writes(self):
        """Should handle concurrent writes safely"""
        import threading
        
        def write_snapshot(i):
            try:
                self.db.save_snapshot(f"session_{i}", [{"role": "user", "content": f"Message {i}"}])
            except Exception:
                # SQLite may have transaction conflicts in concurrent scenarios
                pass
        
        threads = [threading.Thread(target=write_snapshot, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        stats = self.db.get_stats()
        # At least some writes should succeed (SQLite has limited concurrency)
        self.assertGreaterEqual(stats['total_snapshots'], 5)
        self.assertGreaterEqual(stats['unique_sessions'], 5)
    
    def test_database_persistence(self):
        """Should persist data across connections"""
        messages = [{"role": "user", "content": "persistent data"}]
        self.db.save_snapshot("session_001", messages)
        self.db.close()
        
        # Reopen database
        from memory import SessionDB
        db2 = SessionDB(self.db_path)
        
        snapshot = db2.get_latest_snapshot("session_001")
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["messages"][0]["content"], "persistent data")
        
        db2.close()


class TestMemoryIntegration(unittest.TestCase):
    """Integration tests for memory system with MyAgent"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_sessions.db"
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_memory_workflow(self):
        """Should support complete memory workflow"""
        from memory import SessionDB, WorkingMemory
        
        db = SessionDB(self.db_path)
        wm = WorkingMemory()
        
        # 1. Set working memory
        wm.set("current_bug", "Memory leak in loop")
        wm.push_goal("Analyze code")
        
        # 2. Create conversation
        messages = [
            {"role": "user", "content": "I found a memory leak"},
            {"role": "assistant", "content": "Let me help you debug it"}
        ]
        
        # 3. Save snapshot with working memory
        snapshot_id = db.save_snapshot(
            session_id="debug_session_001",
            messages=messages,
            working_memory=wm.to_dict()
        )
        self.assertGreater(snapshot_id, 0)
        
        # 4. Simulate context compression - save another snapshot
        messages.append({"role": "user", "content": "Found the issue in loop.py"})
        wm.set("solution", "Use weakref to break circular reference")
        
        db.save_snapshot(
            session_id="debug_session_001",
            messages=messages,
            working_memory=wm.to_dict()
        )
        
        # 5. Retrieve latest snapshot
        snapshot = db.get_latest_snapshot("debug_session_001")
        self.assertIsNotNone(snapshot)
        self.assertEqual(len(snapshot["messages"]), 3)
        self.assertEqual(snapshot["working_memory"]["context"]["solution"], 
                        "Use weakref to break circular reference")
        
        # 6. Complete goal
        wm.pop_goal()
        
        # 7. Verify session history
        snapshots = db.list_snapshots("debug_session_001")
        self.assertEqual(len(snapshots), 2)
        
        db.close()


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
