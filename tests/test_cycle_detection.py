"""Tests for subagent call-chain cycle detection.

覆盖 bugfix-6 之前的历史用例（从 commit 5584656^ 取回为参考），
对齐 req-28 / chg-04 恢复后的 API。import 入口调整为
``harness_workflow`` 顶层 re-export（旧 ``harness_workflow.core``
路径已废弃）。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow import (  # noqa: E402
    CallChainNode,
    CycleDetectionResult,
    CycleDetector,
    detect_subagent_cycle,
    get_cycle_detector,
    report_cycle_detection,
    reset_cycle_detector,
)


class TestCallChainNode(unittest.TestCase):
    """CallChainNode dataclass."""

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
    """CycleDetector 单例类。"""

    def setUp(self) -> None:
        reset_cycle_detector()
        self.detector = get_cycle_detector()

    def tearDown(self) -> None:
        reset_cycle_detector()

    def test_singleton_get_reset(self) -> None:
        """get_cycle_detector 返回单例；reset 后是新实例。"""
        d1 = get_cycle_detector()
        d2 = get_cycle_detector()
        self.assertIs(d1, d2)
        reset_cycle_detector()
        d3 = get_cycle_detector()
        self.assertIsNot(d1, d3)

    def test_empty_chain_no_cycle(self) -> None:
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
        node_a = CallChainNode(
            level=0, agent_id="agent-a", role="executing", task="Task A",
            session_memory_path="path-a",
        )
        node_b = CallChainNode(
            level=1, agent_id="agent-b", role="testing", task="Task B",
            session_memory_path="path-b", parent_agent_id="agent-a",
        )
        self.assertFalse(self.detector.add_node(node_a).has_cycle)
        self.assertFalse(self.detector.add_node(node_b).has_cycle)
        self.assertEqual(self.detector.get_chain_depth(), 2)

    def test_simple_cycle_detected(self) -> None:
        """A -> B -> A should detect a cycle."""
        node_a = CallChainNode(
            level=0, agent_id="agent-a", role="executing", task="Task A",
            session_memory_path="path-a",
        )
        node_b = CallChainNode(
            level=1, agent_id="agent-b", role="testing", task="Task B",
            session_memory_path="path-b", parent_agent_id="agent-a",
        )
        self.detector.add_node(node_a)
        self.detector.add_node(node_b)

        node_a_again = CallChainNode(
            level=2, agent_id="agent-a", role="executing", task="Task A again",
            session_memory_path="path-c", parent_agent_id="agent-b",
        )
        result = self.detector.add_node(node_a_again)
        self.assertTrue(result.has_cycle)
        self.assertIn("agent-a", result.cycle_path)
        self.assertIn("Cycle detected", result.message)
        # 命中 cycle 时不应把重复节点写入链
        self.assertEqual(self.detector.get_chain_depth(), 2)

    def test_deep_cycle_detected(self) -> None:
        """A -> B -> C -> A should detect a cycle."""
        node_a = CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a")
        node_b = CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a")
        node_c = CallChainNode(level=2, agent_id="agent-c", role="acceptance", task="Task C", session_memory_path="path-c", parent_agent_id="agent-b")
        self.detector.add_node(node_a)
        self.detector.add_node(node_b)
        self.detector.add_node(node_c)

        node_a_again = CallChainNode(
            level=3, agent_id="agent-a", role="executing", task="Task A again",
            session_memory_path="path-d", parent_agent_id="agent-c",
        )
        result = self.detector.add_node(node_a_again)
        self.assertTrue(result.has_cycle)
        self.assertEqual(result.cycle_path, ["agent-a", "agent-b", "agent-c", "agent-a"])

    def test_chain_snapshot(self) -> None:
        node_a = CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a")
        node_b = CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a")
        self.detector.add_node(node_a)
        self.detector.add_node(node_b)
        snapshot = self.detector.get_chain_snapshot()
        self.assertEqual(len(snapshot), 2)
        self.assertEqual(snapshot[0]["agent_id"], "agent-a")
        self.assertEqual(snapshot[1]["agent_id"], "agent-b")
        # snapshot 是深拷贝，修改它不影响内部链
        snapshot[0]["agent_id"] = "mutated"
        self.assertEqual(self.detector.get_chain_snapshot()[0]["agent_id"], "agent-a")

    def test_clear_chain(self) -> None:
        node_a = CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a")
        self.detector.add_node(node_a)
        self.assertEqual(self.detector.get_chain_depth(), 1)
        self.detector.clear()
        self.assertEqual(self.detector.get_chain_depth(), 0)

    def test_pop_node(self) -> None:
        node_a = CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a")
        node_b = CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a")
        self.detector.add_node(node_a)
        self.detector.add_node(node_b)
        popped = self.detector.pop()
        self.assertIsNotNone(popped)
        self.assertEqual(popped.agent_id, "agent-b")
        self.assertEqual(self.detector.get_chain_depth(), 1)
        # 空链 pop 返回 None
        self.detector.clear()
        self.assertIsNone(self.detector.pop())


class TestDetectSubagentCycleFunction(unittest.TestCase):
    """无状态 detect_subagent_cycle 函数。"""

    def test_no_cycle_empty_chain(self) -> None:
        result = detect_subagent_cycle(
            chain=[], new_agent_id="agent-a",
            new_role="executing", new_task="Task A", new_session_memory_path="path-a",
        )
        self.assertFalse(result.has_cycle)

    def test_no_cycle_new_agent(self) -> None:
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
        ]
        result = detect_subagent_cycle(
            chain=chain, new_agent_id="agent-c",
            new_role="acceptance", new_task="Task C", new_session_memory_path="path-c",
        )
        self.assertFalse(result.has_cycle)

    def test_cycle_detected_simple(self) -> None:
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
        ]
        result = detect_subagent_cycle(
            chain=chain, new_agent_id="agent-a",
            new_role="executing", new_task="Task A again", new_session_memory_path="path-c",
        )
        self.assertTrue(result.has_cycle)
        self.assertIn("agent-a -> agent-b -> agent-a", result.message)

    def test_cycle_detected_deep(self) -> None:
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
            CallChainNode(level=2, agent_id="agent-c", role="acceptance", task="Task C", session_memory_path="path-c", parent_agent_id="agent-b"),
        ]
        result = detect_subagent_cycle(
            chain=chain, new_agent_id="agent-a",
            new_role="executing", new_task="Task A again", new_session_memory_path="path-d",
        )
        self.assertTrue(result.has_cycle)
        self.assertEqual(result.cycle_path, ["agent-a", "agent-b", "agent-c", "agent-a"])

    def test_dict_chain_compat(self) -> None:
        """detect_subagent_cycle 兼容 dict 列表（CLI 持久化格式）。"""
        chain = [
            {"agent_id": "agent-a", "role": "executing"},
            {"agent_id": "agent-b", "role": "testing"},
        ]
        result = detect_subagent_cycle(
            chain=chain, new_agent_id="agent-a",
            new_role="executing", new_task="again", new_session_memory_path="path",
        )
        self.assertTrue(result.has_cycle)
        self.assertEqual(result.cycle_path, ["agent-a", "agent-b", "agent-a"])


class TestReportCycleDetection(unittest.TestCase):
    """report_cycle_detection 写入 action-log 与 cycle-logs。"""

    def setUp(self) -> None:
        self.tempdir = tempfile.mkdtemp()
        self.root_path = Path(self.tempdir)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tempdir)

    def test_report_writes_to_action_log(self) -> None:
        action_log_path = self.root_path / ".workflow" / "state" / "action-log.md"
        action_log_path.parent.mkdir(parents=True, exist_ok=True)

        result = CycleDetectionResult(
            has_cycle=True,
            cycle_path=["agent-a", "agent-b", "agent-a"],
            message="Cycle detected: agent-a -> agent-b -> agent-a",
        )
        report_cycle_detection(result, action_log_path, self.root_path)

        self.assertTrue(action_log_path.exists())
        content = action_log_path.read_text(encoding="utf-8")
        self.assertIn("Cycle Detection Alert", content)
        self.assertIn("agent-a -> agent-b -> agent-a", content)

    def test_report_creates_cycle_log(self) -> None:
        action_log_path = self.root_path / ".workflow" / "state" / "action-log.md"
        action_log_path.parent.mkdir(parents=True, exist_ok=True)

        result = CycleDetectionResult(
            has_cycle=True,
            cycle_path=["agent-x", "agent-y", "agent-x"],
            message="Cycle detected: agent-x -> agent-y -> agent-x",
        )
        report_cycle_detection(result, action_log_path, self.root_path)

        cycle_log_dir = self.root_path / ".workflow" / "state" / "cycle-logs"
        self.assertTrue(cycle_log_dir.exists())
        cycle_logs = list(cycle_log_dir.glob("cycle-*.md"))
        self.assertEqual(len(cycle_logs), 1)
        self.assertIn(
            "agent-x -> agent-y -> agent-x",
            cycle_logs[0].read_text(encoding="utf-8"),
        )

    def test_report_noop_when_no_cycle(self) -> None:
        """has_cycle=False 时不写任何文件。"""
        action_log_path = self.root_path / ".workflow" / "state" / "action-log.md"
        action_log_path.parent.mkdir(parents=True, exist_ok=True)

        result = CycleDetectionResult(has_cycle=False, cycle_path=[], message="")
        report_cycle_detection(result, action_log_path, self.root_path)
        self.assertFalse(action_log_path.exists())
        cycle_log_dir = self.root_path / ".workflow" / "state" / "cycle-logs"
        self.assertFalse(cycle_log_dir.exists())


class TestCycleDetectionScenarios(unittest.TestCase):
    """AC 场景覆盖。"""

    def test_scenario_a_b_a_cycle(self) -> None:
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
        ]
        result = detect_subagent_cycle(
            chain=chain, new_agent_id="agent-a",
            new_role="executing", new_task="Task A from B", new_session_memory_path="path-c",
        )
        self.assertTrue(result.has_cycle)
        self.assertEqual(result.cycle_path, ["agent-a", "agent-b", "agent-a"])
        self.assertIn("agent-a -> agent-b -> agent-a", result.message)

    def test_scenario_a_b_c_a_deep_cycle(self) -> None:
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="planning", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
            CallChainNode(level=2, agent_id="agent-c", role="testing", task="Task C", session_memory_path="path-c", parent_agent_id="agent-b"),
        ]
        result = detect_subagent_cycle(
            chain=chain, new_agent_id="agent-a",
            new_role="executing", new_task="Task A from C", new_session_memory_path="path-d",
        )
        self.assertTrue(result.has_cycle)
        self.assertEqual(result.cycle_path, ["agent-a", "agent-b", "agent-c", "agent-a"])
        self.assertIn("agent-a -> agent-b -> agent-c -> agent-a", result.message)

    def test_normal_chain_not_affected(self) -> None:
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
            CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
        ]
        result = detect_subagent_cycle(
            chain=chain, new_agent_id="agent-c",
            new_role="acceptance", new_task="Task C", new_session_memory_path="path-c",
        )
        self.assertFalse(result.has_cycle)

    def test_sibling_agents_no_cycle(self) -> None:
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
        ]
        result_b = detect_subagent_cycle(
            chain=chain, new_agent_id="agent-b",
            new_role="testing", new_task="Task B", new_session_memory_path="path-b",
        )
        self.assertFalse(result_b.has_cycle)

        result_c = detect_subagent_cycle(
            chain=[
                CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
                CallChainNode(level=1, agent_id="agent-b", role="testing", task="Task B", session_memory_path="path-b", parent_agent_id="agent-a"),
            ],
            new_agent_id="agent-c",
            new_role="acceptance", new_task="Task C", new_session_memory_path="path-c",
        )
        self.assertFalse(result_c.has_cycle)

    def test_same_role_different_agent_is_not_cycle(self) -> None:
        """同 role 不同 agent_id 不视为 cycle（判定依据是 agent_id）。"""
        chain = [
            CallChainNode(level=0, agent_id="agent-a", role="executing", task="Task A", session_memory_path="path-a"),
        ]
        result = detect_subagent_cycle(
            chain=chain, new_agent_id="agent-a2",
            new_role="executing", new_task="Task A2", new_session_memory_path="path-a2",
        )
        self.assertFalse(result.has_cycle)


class TestCycleDetectorModuleSmoke(unittest.TestCase):
    """保留 bugfix-6 smoke 测试：CLI 模块仍可 import、main 可调用。"""

    def test_cli_module_importable(self) -> None:
        import importlib
        module = importlib.import_module(
            "harness_workflow.tools.harness_cycle_detector"
        )
        self.assertTrue(hasattr(module, "main"))
        self.assertTrue(callable(module.main))
        # CLI 模块也应 re-export 这些符号
        for name in (
            "CallChainNode", "CycleDetector", "CycleDetectionResult",
            "detect_subagent_cycle", "report_cycle_detection",
            "get_cycle_detector", "reset_cycle_detector",
        ):
            self.assertTrue(hasattr(module, name), f"missing re-export: {name}")


if __name__ == "__main__":
    unittest.main()
