"""req-29 / chg-03：决策点数据模型与决策汇总渲染的单元测试。

覆盖：
- ``append_decision`` 自动建文件、建表头、分配 ``dec-NNN`` id；
- ``read_decision_log`` 与 ``append_decision`` 的往返一致性；
- ``render_decision_summary`` 按 high → medium → low 分组；
- ``write_decision_summary`` 路径契约（artifacts/{branch}/.../决策汇总.md）；
- ``is_blocking_decision`` 对 5.1 阻塞清单的 keyword 命中与非命中场景。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from harness_workflow.decision_log import (  # noqa: E402  (path inject above)
    BLOCKING_CATEGORIES,
    DecisionPoint,
    append_decision,
    is_blocking_decision,
    read_decision_log,
    render_decision_summary,
    write_decision_summary,
)


def _dp(
    *,
    id_: str = "",
    ts: str = "2026-04-19T10:00:00Z",
    stage: str = "planning",
    risk: str = "low",
    description: str = "测试描述",
    options: list[str] | None = None,
    choice: str = "A",
    reason: str = "默认理由",
) -> DecisionPoint:
    return DecisionPoint(
        id=id_,
        timestamp=ts,
        stage=stage,
        risk=risk,
        description=description,
        options=list(options) if options is not None else ["A", "B"],
        choice=choice,
        reason=reason,
    )


class DecisionLogAppendTests(unittest.TestCase):
    def test_append_decision_creates_file_with_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / ".workflow" / "flow" / "requirements" / "req-99" / "decisions-log.md"
            self.assertFalse(path.exists())
            append_decision(root, "req-99", _dp())
            self.assertTrue(path.exists())
            text = path.read_text(encoding="utf-8")
            # 表头存在；至少有一条 fenced YAML block。
            self.assertTrue(text.startswith("# Decisions Log"))
            self.assertIn("```yaml decision", text)
            self.assertIn('id: "dec-001"', text)

    def test_append_decision_monotonic_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(3):
                append_decision(root, "req-99", _dp(description=f"第 {i} 条"))
            points = read_decision_log(root, "req-99")
            self.assertEqual([p.id for p in points], ["dec-001", "dec-002", "dec-003"])

    def test_append_decision_preserves_explicit_id(self) -> None:
        """调用方显式给 id 时，本函数不覆盖，仅按传入值写入。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            append_decision(root, "req-99", _dp(id_="dec-042"))
            points = read_decision_log(root, "req-99")
            self.assertEqual([p.id for p in points], ["dec-042"])
            # 继续 append 时自动从 dec-043 起跳。
            append_decision(root, "req-99", _dp(description="下一条"))
            points = read_decision_log(root, "req-99")
            self.assertEqual([p.id for p in points], ["dec-042", "dec-043"])


class DecisionLogRoundtripTests(unittest.TestCase):
    def test_read_decision_log_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            originals = [
                _dp(description="决策 1", options=["选项 A", "选项 B"], choice="选项 A", reason="理由 1"),
                _dp(
                    description='含 " 双引号 与 \\ 反斜杠',
                    options=['opt "1"', 'opt \\2'],
                    choice='opt "1"',
                    reason="escape 测试",
                    risk="medium",
                ),
                _dp(
                    description="无选项场景",
                    options=[],
                    choice="-",
                    reason="无可选项",
                    risk="high",
                    stage="executing",
                ),
            ]
            for p in originals:
                append_decision(root, "req-99", p)

            readback = read_decision_log(root, "req-99")
            self.assertEqual(len(readback), len(originals))
            for orig, got in zip(originals, readback):
                # id 由 append_decision 自动分配，单独断言其余字段。
                self.assertEqual(got.timestamp, orig.timestamp)
                self.assertEqual(got.stage, orig.stage)
                self.assertEqual(got.risk, orig.risk)
                self.assertEqual(got.description, orig.description)
                self.assertEqual(got.options, list(orig.options))
                self.assertEqual(got.choice, orig.choice)
                self.assertEqual(got.reason, orig.reason)

    def test_read_decision_log_missing_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(read_decision_log(root, "req-not-exists"), [])


class DecisionSummaryRenderTests(unittest.TestCase):
    def test_render_summary_groups_by_risk(self) -> None:
        points = [
            _dp(id_="dec-001", risk="low", description="低风险 A"),
            _dp(id_="dec-002", risk="high", description="高风险 B"),
            _dp(id_="dec-003", risk="medium", description="中风险 C"),
            _dp(id_="dec-004", risk="high", description="高风险 D"),
            _dp(id_="dec-005", risk="low", description="低风险 E"),
        ]
        text = render_decision_summary(points)
        # 顶部汇总计数正确。
        self.assertIn("共 5 条自主决策点：high=2，medium=1，low=2", text)
        # 分组顺序：high → medium → low。
        high_idx = text.index("## 高风险决策")
        medium_idx = text.index("## 中风险决策")
        low_idx = text.index("## 低风险决策")
        self.assertLess(high_idx, medium_idx)
        self.assertLess(medium_idx, low_idx)
        # 高风险段内既有 B 也有 D，且都在 medium 段之前出现。
        high_block = text[high_idx:medium_idx]
        self.assertIn("dec-002", high_block)
        self.assertIn("dec-004", high_block)
        # 低风险段包含 A 和 E。
        low_block = text[low_idx:]
        self.assertIn("dec-001", low_block)
        self.assertIn("dec-005", low_block)

    def test_render_summary_empty_points(self) -> None:
        text = render_decision_summary([])
        self.assertIn("共 0 条自主决策点", text)
        self.assertIn("未产生自主决策点", text)


class DecisionSummaryWriteTests(unittest.TestCase):
    def test_write_summary_to_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 先建好 requirement 目录，触发 slug 推断。
            req_dir = root / "artifacts" / "main" / "requirements" / "req-99-demo-summary"
            req_dir.mkdir(parents=True)
            append_decision(root, "req-99", _dp(risk="high", description="高风险 X"))
            append_decision(root, "req-99", _dp(risk="low", description="低风险 Y"))

            target = write_decision_summary(root, "req-99", "main")
            self.assertEqual(target, req_dir / "决策汇总.md")
            self.assertTrue(target.exists())
            content = target.read_text(encoding="utf-8")
            self.assertIn("# 决策汇总", content)
            self.assertIn("高风险 X", content)
            self.assertIn("低风险 Y", content)

    def test_write_summary_falls_back_when_no_slug_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 不建 requirement 目录，函数应自己创建 {req_id} 目录兜底。
            append_decision(root, "req-77", _dp())
            target = write_decision_summary(root, "req-77", "main")
            self.assertEqual(target.name, "决策汇总.md")
            self.assertTrue(target.exists())


class BlockingDecisionTests(unittest.TestCase):
    def test_blocking_categories_are_frozen(self) -> None:
        # 与 requirement.md 5.1 的 8 条对齐。
        self.assertEqual(len(BLOCKING_CATEGORIES), 8)

    def test_is_blocking_decision_detects_rm_rf(self) -> None:
        d = _dp(description="rm -rf dist 目录", options=["rm -rf", "保留"], choice="rm -rf", reason="清理")
        self.assertTrue(is_blocking_decision(d))

    def test_is_blocking_decision_detects_force_push(self) -> None:
        d = _dp(description="是否 git push --force", options=["push --force", "放弃"], choice="push --force", reason="强推")
        self.assertTrue(is_blocking_decision(d))

    def test_is_blocking_decision_ignores_low_risk(self) -> None:
        d = _dp(description="选 A 还是 B 命名", options=["A", "B"], choice="A", reason="A 简单")
        self.assertFalse(is_blocking_decision(d))

    def test_is_blocking_decision_detects_dependency_change(self) -> None:
        d = _dp(description="在 pyproject.toml 新增依赖 foo", options=["新增", "不加"], choice="新增", reason="需要")
        self.assertTrue(is_blocking_decision(d))


if __name__ == "__main__":
    unittest.main()
