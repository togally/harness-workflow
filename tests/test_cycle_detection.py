"""Tests for subagent call chain cycle detection."""

import tempfile
import unittest
from pathlib import Path

from harness_workflow.core import (
    CallChainNode,
    CycleDetectionResult,
    CycleDetector,
    detect_subagent_cycle,
    report_cycle_detection,
    get_cycle_detector,
    reset_cycle_detector,
)


class TestCallChainNode(unittest.TestCase):
    """Test CallChainNode dataclass."""

    def test_create_node(self) -> None:
        node = CallChainNode(
            level=0,
            agent_id="agent-1",
            role="executing",
            task="Execute change",
            session_memory_path=".workflow/state/sessions/req-01/chg-01/session-memory.md",
        )
        self.assertEqual(node.level, 0)
        self.assertEqual(node.agent_id, "agent-1")
        self.assertEqual(node.role, "executing")
        self.assertEqual(node.task, "Execute change")
        self.assertIsNone(node.parent_agent_id)

    def test_create_node_with_parent(self) -> None:
        node = CallChainNode(
            level=1,
            agent_id="agent-2",
            role="testing",
            task="Run tests",
            session_memory_path=".workflow/state/sessions/req-01/chg-01/session-memory.md",
            parent_agent_id="agent-1",
        )
        self.assertEqual(node.parent_agent_id, "agent-1")


class TestCycleDetector(unittest.TestCase):
    """Test CycleDetector class."""

    def setUp(self) -> None:
        reset_cycle_detector()
        self.detector = get_cycle_detector()

    def tearDown(self) -> None:
        reset_cycle_detector()

    def test_empty_chain_no_cycle(self) -> None:
        """Adding first node should never create a cycle."""
        node = CallChainNode(
            level=0,
            agent_id="agent-1",
            role="executing",
            task="Execute change",
            session_memory_path=".workflow/state/sessions/req-01/chg-01/session-memory.md",
        )
        result = self.detector.add_node(node)
        self.assertFalse(result.has_cycle)
        self.assertEqual(self.detector.get_chain_depth(), 1)

    def test_simple_chain_no_cycle(self) -> None:
        """A -> B should not create a cycle."""
        node_a = CallChainNode(
            level=0,
            agent_id="agent-a",
            role="executing",
            task="Task A",
            session_memory_path=".workflow/state/sessions/req-01/chg-01/session-memory.md",
        )
        node_b = CallChainNode(
            level=1,
            agent_id="agent-b",
            role="testing",
            task="Task B",
            session_memory_path=".workflow/state/sessions/req-01/chg-02/session-memory.md",
            parent_agent_id="agent-a",
        )

        result_a = self.detector.add_node(node_a)
        self.assertFalse(result_a.has_cycle)

        result_b = self.detector.add_node(node_b)
        self.assertFalse(result_b.has_cycle)
        self.assertEqual(self.detector.get_chain_depth(), 2)

    def test_simple_cycle_detected(self) -> None:
        """A -> B -> A should detect a cycle."""
        node_a = CallChainNode(
            level=0,
            agent_id="agent-a",
            role="executing",
            task="Task A",
            session_memory_path=".workflow/state/sessions/req-01/chg-01/session-memory.md",
        )
        node_b = CallChainNode(
            level=1,
            agent_id="agent-b",
            role="testing",
            task="Task B",
            session_memory_path=".workflow/state/sessions/req-01/chg-02/session-memory.md",
            parent_agent_id="agent-a",
        )

        self.detector.add_node(node_a)
        self.detector.add_node(node_b)

        # Now try to add agent-a again (would create A -> B -> A cycle)
        node_a_again = CallChainNode(
            level=2,
            agent_id="agent-a",  # Same as first node!
            role="executing",
            task="Task A again",
            session_memory_path=".workflow/state/sessions/req-01/chg-03/session-memory.md",
            parent_agent_id="agent-b",
        )
        result = self.detector.add_node(node_a_again)

        self.assertTrue(result.has_cycle)
        self.assertIn("agent-a", result.cycle_path)
        self.assertIn("Cycle detected", result.message)

    def test_deep_cycle_detected(self) -> None:
        """A -> B -> C -> A should detect a cycle."""
        node_a = CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a")
        node_b = CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a")
        node_c = CallChainNode(level=2, agent_id="agent-c", role="acceptance", task="Task C", session_memory_path="path-c", parent_agent_id="agent-b")

        self.detector.add_node(node_a)
        self.detector.add_node(node_b)
        self.detector.add_node(node_c)

        # Now try to add agent-a again (would create A -> B -> C -> A cycle)
        node_a_again = CallChainNode(
            level=3,
            agent_id="agent-a",  # Same as first node!
            role="executing",
            task="Task A again",
            session_memory_path="path-d",
            parent_agent_id="agent-c",
        )
        result = self.detector.add_node(node_a_again)

        self.assertTrue(result.has_cycle)
        self.assertEqual(len(result.cycle_path), 4)  # A -> B -> C -> A
        self.assertEqual(result.cycle_path, ["agent-a", "agent-b", "agent-c", "agent-a"])

    def test_chain_snapshot(self) -> None:
        """Test getting a snapshot of the chain."""
        node_a = CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a")
        node_b = CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a")

        self.detector.add_node(node_a)
        self.detector.add_node(node_b)

        snapshot = self.detector.get_chain_snapshot()
        self.assertEqual(len(snapshot), 2)
        self.assertEqual(snapshot[0]["agent_id"], "agent-a")
        self.assertEqual(snapshot[1]["agent_id"], "agent-b")

    def test_clear_chain(self) -> None:
        """Test clearing the chain."""
        node_a = CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a")
        self.detector.add_node(node_a)
        self.assertEqual(self.detector.get_chain_depth(), 1)

        self.detector.clear()
        self.assertEqual(self.detector.get_chain_depth(), 0)

    def test_pop_node(self) -> None:
        """Test popping a node from the chain."""
        node_a = CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a")
        node_b = CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a")

        self.detector.add_node(node_a)
        self.detector.add_node(node_b)

        popped = self.detector.pop()
        self.assertEqual(popped.agent_id, "agent-b")
        self.assertEqual(self.detector.get_chain_depth(), 1)


class TestDetectSubagentCycleFunction(unittest.TestCase):
    """Test the standalone detect_subagent_cycle function."""

    def test_no_cycle_empty_chain(self) -> None:
        """Empty chain should never detect a cycle."""
        result = detect_subagent_cycle(
            chain=[],
            new_agent_id="agent-a",
            new_role="executing",
            new_task="Task A",
            new_session_memory_path="path-a",
        )
        self.assertFalse(result.has_cycle)

    def test_no_cycle_new_agent(self) -> None:
        """Adding a new agent not in chain should not create cycle."""
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
        ]
        result = detect_subagent_cycle(
            chain=chain,
            new_agent_id="agent-c",
            new_role="acceptance",
            new_task="Task C",
            new_session_memory_path="path-c",
        )
        self.assertFalse(result.has_cycle)

    def test_cycle_detected_simple(self) -> None:
        """A -> B -> A should detect a cycle."""
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
        ]
        result = detect_subagent_cycle(
            chain=chain,
            new_agent_id="agent-a",  # Trying to add agent-a again
            new_role="executing",
            new_task="Task A again",
            new_session_memory_path="path-c",
        )
        self.assertTrue(result.has_cycle)
        self.assertIn("agent-a -> agent-b -> agent-a", result.message)

    def test_cycle_detected_deep(self) -> None:
        """A -> B -> C -> A should detect a cycle."""
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
            CallChainNode(level=2, agent_id="agent-c", role="acceptance", task="Task C", session_memory_path="path-c", parent_agent_id="agent-b"),
        ]
        result = detect_subagent_cycle(
            chain=chain,
            new_agent_id="agent-a",  # Trying to add agent-a again
            new_role="executing",
            new_task="Task A again",
            new_session_memory_path="path-d",
        )
        self.assertTrue(result.has_cycle)
        self.assertIn("agent-a", result.cycle_path)
        self.assertIn("agent-b", result.cycle_path)
        self.assertIn("agent-c", result.cycle_path)


class TestReportCycleDetection(unittest.TestCase):
    """Test cycle detection reporting."""

    def setUp(self) -> None:
        self.tempdir = tempfile.mkdtemp()
        self.root_path = Path(self.tempdir)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tempdir)

    def test_report_writes_to_action_log(self) -> None:
        """Test that cycle detection is reported to action log."""
        action_log_path = self.root_path / ".workflow" / "state" / "action-log.md"
        action_log_path.parent.mkdir(parents=True, exist_ok=True)

        result = CycleDetectionResult(
            has_cycle=True,
            cycle_path=["agent-a", "agent-b", "agent-a"],
            message="Cycle detected: agent-a -> agent-b -> agent-a",
        )

        report_cycle_detection(result, action_log_path, self.root_path)

        # Verify action log was created and contains the report
        self.assertTrue(action_log_path.exists())
        content = action_log_path.read_text(encoding="utf-8")
        self.assertIn("Cycle Detection Alert", content)
        self.assertIn("agent-a -> agent-b -> agent-a", content)

    def test_report_creates_cycle_log(self) -> None:
        """Test that cycle detection creates a dedicated log file."""
        action_log_path = self.root_path / ".workflow" / "state" / "action-log.md"
        action_log_path.parent.mkdir(parents=True, exist_ok=True)

        result = CycleDetectionResult(
            has_cycle=True,
            cycle_path=["agent-x", "agent-y", "agent-x"],
            message="Cycle detected: agent-x -> agent-y -> agent-x",
        )

        report_cycle_detection(result, action_log_path, self.root_path)

        # Verify cycle log directory and file were created
        cycle_log_dir = self.root_path / ".workflow" / "state" / "cycle-logs"
        self.assertTrue(cycle_log_dir.exists())
        cycle_logs = list(cycle_log_dir.glob("cycle-*.md"))
        self.assertEqual(len(cycle_logs), 1)
        self.assertIn("agent-x -> agent-y -> agent-x", cycle_logs[0].read_text(encoding="utf-8"))


class TestCycleDetectionScenarios(unittest.TestCase):
    """Test various cycle detection scenarios from the acceptance criteria."""

    def test_scenario_a_b_a_cycle(self) -> None:
        """A -> B -> A cycle should be detected and terminated."""
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
        ]

        # Try to spawn agent-a from agent-b (A -> B -> A)
        result = detect_subagent_cycle(
            chain=chain,
            new_agent_id="agent-a",
            new_role="executing",
            new_task="Task A from B",
            new_session_memory_path="path-c",
        )

        self.assertTrue(result.has_cycle)
        self.assertEqual(result.cycle_path, ["agent-a", "agent-b", "agent-a"])
        self.assertIn("agent-a -> agent-b -> agent-a", result.message)

    def test_scenario_a_b_c_a_deep_cycle(self) -> None:
        """A -> B -> C -> A deep cycle should be detected and terminated."""
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="planning", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
            CallChainNode(level=2, agent_id="agent-c", role="testing", task="Task C", session_memory_path="path-c", parent_agent_id="agent-b"),
        ]

        # Try to spawn agent-a from agent-c (A -> B -> C -> A)
        result = detect_subagent_cycle(
            chain=chain,
            new_agent_id="agent-a",
            new_role="executing",
            new_task="Task A from C",
            new_session_memory_path="path-d",
        )

        self.assertTrue(result.has_cycle)
        self.assertEqual(result.cycle_path, ["agent-a", "agent-b", "agent-c", "agent-a"])
        self.assertIn("agent-a -> agent-b -> agent-c -> agent-a", result.message)

    def test_normal_chain_not_affected(self) -> None:
        """Normal call chains (A -> B -> C) should not be affected."""
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
        ]

        # Add agent-c (normal case, no cycle)
        result = detect_subagent_cycle(
            chain=chain,
            new_agent_id="agent-c",
            new_role="acceptance",
            new_task="Task C",
            new_session_memory_path="path-c",
        )

        self.assertFalse(result.has_cycle)

    def test_sibling_agents_no_cycle(self) -> None:
        """Spawning different agents should not create cycles."""
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
        ]

        # Spawn agent-b
        result_b = detect_subagent_cycle(
            chain=chain,
            new_agent_id="agent-b",
            new_role="testing",
            new_task="Task B",
            new_session_memory_path="path-b",
        )
        self.assertFalse(result_b.has_cycle)

        # Spawn agent-c from same parent (sibling, not a cycle)
        result_c = detect_subagent_cycle(
            chain=[
                CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
                CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
            ],
            new_agent_id="agent-c",
            new_role="acceptance",
            new_task="Task C",
            new_session_memory_path="path-c",
        )
        self.assertFalse(result_c.has_cycle)


if __name__ == "__main__":
    unittest.main()
