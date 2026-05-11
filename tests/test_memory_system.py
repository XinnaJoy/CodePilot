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


class TestMemoryDB(unittest.TestCase):
    """Test MemoryDB class (SQLite persistence)"""
    
    def setUp(self):
        """Create temporary database for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_memory.db"
        
        from memory import MemoryDB
        self.db = MemoryDB(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    # === Knowledge Tests ===
    
    def test_store_knowledge(self):
        """Should store knowledge entry"""
        result = self.db.store_knowledge(
            category="code_pattern",
            key="singleton_pattern",
            content="Use __new__ for singleton in Python",
            tags=["python", "design-pattern"]
        )
        self.assertIsInstance(result, int)
        self.assertGreater(result, 0)
    
    def test_store_duplicate_knowledge_updates(self):
        """Should update existing knowledge on duplicate key"""
        self.db.store_knowledge("api_usage", "openai", "Old content")
        self.db.store_knowledge("api_usage", "openai", "New content")
        
        results = self.db.search_knowledge("openai")
        self.assertEqual(len(results), 1)
        self.assertIn("New content", results[0]['content'])
    
    def test_search_knowledge_by_content(self):
        """Should find knowledge by content match"""
        self.db.store_knowledge("code_pattern", "factory", "Factory pattern creates objects")
        self.db.store_knowledge("code_pattern", "builder", "Builder pattern constructs complex objects")
        
        results = self.db.search_knowledge("Factory")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['key'], "factory")
    
    def test_search_knowledge_by_category(self):
        """Should filter knowledge by category"""
        self.db.store_knowledge("code_pattern", "singleton", "Singleton content")
        self.db.store_knowledge("api_usage", "redis", "Redis content")
        
        results = self.db.search_knowledge("content", category="code_pattern")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['category'], "code_pattern")
    
    def test_search_knowledge_empty_query(self):
        """Should handle empty query gracefully"""
        self.db.store_knowledge("test", "key1", "content1")
        
        results = self.db.search_knowledge("")
        # Should return empty or handle gracefully
        self.assertIsInstance(results, list)
    
    def test_knowledge_access_count_increments(self):
        """Should increment access_count on retrieval"""
        self.db.store_knowledge("test", "popular", "Popular content")
        
        self.db.search_knowledge("Popular")
        self.db.search_knowledge("Popular")
        
        results = self.db.search_knowledge("Popular")
        self.assertGreaterEqual(results[0]['access_count'], 2)
    
    # === Experience Tests ===
    
    def test_store_experience(self):
        """Should store problem-solution experience"""
        result = self.db.store_experience(
            problem="NullPointerException in UserService",
            solution="Added null check before accessing user.profile",
            success=True,
            context={"file": "UserService.py", "line": 42}
        )
        self.assertIsInstance(result, int)
        self.assertGreater(result, 0)
    
    def test_search_experience_success_only(self):
        """Should filter successful experiences by default"""
        self.db.store_experience("Bug A", "Solution A", success=True)
        self.db.store_experience("Bug B", "Failed attempt", success=False)
        
        results = self.db.search_experience("Bug", success_only=True)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['success'])
    
    def test_search_experience_include_failures(self):
        """Should include failures when requested"""
        self.db.store_experience("Bug A", "Solution A", success=True)
        self.db.store_experience("Bug B", "Failed attempt", success=False)
        
        results = self.db.search_experience("Bug", success_only=False)
        self.assertEqual(len(results), 2)
    
    def test_experience_reuse_count_increments(self):
        """Should increment reuse_count on retrieval"""
        self.db.store_experience("Common bug", "Common fix", success=True)
        
        self.db.search_experience("Common")
        self.db.search_experience("Common")
        
        results = self.db.search_experience("Common")
        self.assertGreaterEqual(results[0]['reuse_count'], 2)
    
    # === FTS5 Full-Text Search Tests ===
    
    def test_fts5_phrase_search(self):
        """Should support phrase search with FTS5"""
        self.db.store_knowledge("test", "k1", "async await pattern in Python")
        self.db.store_knowledge("test", "k2", "Python async programming")
        
        results = self.db.search_knowledge("async await")
        self.assertGreater(len(results), 0)
    
    def test_fts5_handles_special_characters(self):
        """Should handle special characters in search"""
        self.db.store_knowledge("test", "k1", "Use @decorator syntax")
        
        # Should not crash on special chars
        results = self.db.search_knowledge("@decorator")
        self.assertIsInstance(results, list)
    
    # === Statistics Tests ===
    
    def test_get_stats_empty_db(self):
        """Should return zero stats for empty database"""
        stats = self.db.get_stats()
        
        self.assertEqual(stats['knowledge_entries'], 0)
        self.assertEqual(stats['successful_experiences'], 0)
        self.assertEqual(stats['failed_experiences'], 0)
        self.assertGreaterEqual(stats['db_size_kb'], 0)
    
    def test_get_stats_with_data(self):
        """Should return accurate statistics"""
        self.db.store_knowledge("test", "k1", "content1")
        self.db.store_knowledge("test", "k2", "content2")
        self.db.store_experience("p1", "s1", success=True)
        self.db.store_experience("p2", "s2", success=False)
        
        stats = self.db.get_stats()
        
        self.assertEqual(stats['knowledge_entries'], 2)
        self.assertEqual(stats['successful_experiences'], 1)
        self.assertEqual(stats['failed_experiences'], 1)
        self.assertGreater(stats['db_size_kb'], 0)
    
    # === Edge Cases ===
    
    def test_large_content_storage(self):
        """Should handle large content (50KB+)"""
        large_content = "x" * 60000  # 60KB
        
        result = self.db.store_knowledge("test", "large", large_content)
        self.assertIsInstance(result, int)
        
        results = self.db.search_knowledge("large")
        self.assertEqual(len(results[0]['content']), 60000)
    
    def test_unicode_content(self):
        """Should handle Unicode characters"""
        self.db.store_knowledge("test", "unicode", "中文内容 🚀 émojis")
        
        results = self.db.search_knowledge("中文")
        self.assertEqual(len(results), 1)
        self.assertIn("中文内容", results[0]['content'])
    
    def test_concurrent_writes(self):
        """Should handle concurrent writes safely"""
        import threading
        
        def write_knowledge(i):
            self.db.store_knowledge("test", f"key{i}", f"content{i}")
        
        threads = [threading.Thread(target=write_knowledge, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        stats = self.db.get_stats()
        self.assertEqual(stats['knowledge_entries'], 10)
    
    def test_search_limit_parameter(self):
        """Should respect limit parameter"""
        for i in range(10):
            self.db.store_knowledge("test", f"k{i}", "searchable content")
        
        results = self.db.search_knowledge("searchable", limit=3)
        self.assertEqual(len(results), 3)
    
    def test_database_persistence(self):
        """Should persist data across connections"""
        self.db.store_knowledge("test", "persist", "persistent data")
        self.db.close()
        
        # Reopen database
        from memory import MemoryDB
        db2 = MemoryDB(self.db_path)
        
        results = db2.search_knowledge("persistent")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['key'], "persist")
        
        db2.close()


class TestMemoryIntegration(unittest.TestCase):
    """Integration tests for memory system with MyAgent"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_memory.db"
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_memory_workflow(self):
        """Should support complete memory workflow"""
        from memory import MemoryDB, WorkingMemory
        
        db = MemoryDB(self.db_path)
        wm = WorkingMemory()
        
        # 1. Set working memory
        wm.set("current_bug", "Memory leak in loop")
        wm.push_goal("Analyze code")
        
        # 2. Search for similar past experiences
        results = db.search_experience("memory leak")
        self.assertEqual(len(results), 0)  # No history yet
        
        # 3. Store solution as experience
        db.store_experience(
            problem="Memory leak in loop",
            solution="Used weakref to break circular reference",
            success=True,
            context={"file": "main.py"}
        )
        
        # 4. Store as knowledge for future
        db.store_knowledge(
            category="best_practice",
            key="memory_leak_fix",
            content="Use weakref for circular references",
            tags=["python", "memory"]
        )
        
        # 5. Verify retrieval
        exp_results = db.search_experience("memory leak")
        self.assertEqual(len(exp_results), 1)
        
        know_results = db.search_knowledge("weakref")
        self.assertEqual(len(know_results), 1)
        
        # 6. Complete goal
        wm.pop_goal()
        
        db.close()


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
