import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "agents"))

from agent_loop import run_agent_loop
from tests.helpers import (
    FakeModelClient,
    FakeResponse,
    StubBackground,
    StubBus,
    StubTodo,
    make_context,
    text_block,
    tool_use_block,
)


class TestAgentRuntime(unittest.TestCase):
    def test_tool_round_trip_then_final_response(self):
        responses = [
            FakeResponse([tool_use_block("tool-1", "bash", command="echo hello")], "tool_use"),
            FakeResponse([text_block("done")], "end_turn"),
        ]
        client = FakeModelClient(responses)
        with tempfile.TemporaryDirectory() as tmp:
            context = make_context(client, Path(tmp))
            messages = [{"role": "user", "content": "say hi"}]
            handlers = {"bash": lambda command: f"ran {command}"}

            run_agent_loop(messages, context, [], handlers, "system", token_threshold=999999)

        self.assertEqual(messages[-1]["role"], "assistant")
        self.assertEqual(messages[-1]["content"][0].text, "done")
        tool_result_message = messages[-2]
        self.assertEqual(tool_result_message["role"], "user")
        self.assertEqual(tool_result_message["content"][0]["type"], "tool_result")
        self.assertEqual(tool_result_message["content"][0]["content"], "ran echo hello")

    def test_open_todos_trigger_reminder_after_three_rounds(self):
        responses = [FakeResponse([tool_use_block(f"tool-{idx}", "bash", command="echo")], "tool_use") for idx in range(3)]
        responses.append(FakeResponse([text_block("finished")], "end_turn"))
        client = FakeModelClient(responses)
        with tempfile.TemporaryDirectory() as tmp:
            context = make_context(client, Path(tmp), todo=StubTodo(has_open=True))
            messages = [{"role": "user", "content": "work"}]
            handlers = {"bash": lambda command: f"ok {command}"}

            run_agent_loop(messages, context, [], handlers, "system", token_threshold=999999)

        reminder_payload = messages[-2]["content"]
        self.assertEqual(reminder_payload[-1]["type"], "text")
        self.assertIn("Update your todos", reminder_payload[-1]["text"])

    def test_background_and_inbox_are_injected_before_model_call(self):
        responses = [FakeResponse([text_block("done")], "end_turn")]
        client = FakeModelClient(responses)
        background = StubBackground([{"task_id": "bg-1", "status": "completed", "result": "ok"}])
        bus = StubBus([{"from": "dev", "content": "ping"}])
        with tempfile.TemporaryDirectory() as tmp:
            context = make_context(client, Path(tmp), background=background, bus=bus)
            messages = [{"role": "user", "content": "start"}]

            run_agent_loop(messages, context, [], {}, "system", token_threshold=999999)

        model_messages = client.calls[0]["messages"]
        self.assertIn("<background-results>", model_messages[1]["content"])
        self.assertIn("<inbox>", model_messages[2]["content"])

    def test_auto_compact_uses_runtime_transcript_dir(self):
        responses = [FakeResponse([text_block("done")], "end_turn")]
        client = FakeModelClient(responses)
        with tempfile.TemporaryDirectory() as tmp:
            context = make_context(client, Path(tmp))
            messages = [{"role": "user", "content": "x" * 200}]

            with patch("agent_loop.auto_compact", return_value=[{"role": "user", "content": "compact"}]) as compact:
                run_agent_loop(messages, context, [], {}, "system", token_threshold=1)

        compact.assert_called_once()
        self.assertEqual(compact.call_args.args[3], context.config.transcript_dir)


if __name__ == "__main__":
    unittest.main()
