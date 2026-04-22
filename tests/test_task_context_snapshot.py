"""req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）

覆盖 `_write_task_context_snapshot` helper：
- frontmatter + 正文
- {seq} 递增（同 req 同 stage）
- 不同 stage seq 独立计数
"""

from __future__ import annotations

from pathlib import Path


def test_snapshot_frontmatter_and_body(tmp_path):
    """req-32 / chg-03 Step 3：落盘文件 frontmatter 四字段齐全，正文每行 {path}: {reason}。"""
    from harness_workflow.workflow_helpers import _write_task_context_snapshot

    root = tmp_path
    index = [
        {"path": ".workflow/context/roles/executing.md", "reason": "当前 stage 角色文件"},
        {"path": ".workflow/context/roles/base-role.md", "reason": "通用规约"},
    ]
    snap = _write_task_context_snapshot(root=root, req_id="req-99", stage="executing", index=index)

    assert snap.exists()
    assert snap.name == "executing-001.md"
    # 路径形态：.workflow/state/sessions/req-99/task-context/executing-001.md
    assert snap.parent == root / ".workflow/state/sessions/req-99/task-context"

    text = snap.read_text(encoding="utf-8")
    # frontmatter
    assert text.startswith("---\n")
    assert "req_id: req-99" in text
    assert "stage: executing" in text
    assert "ts:" in text
    assert "index_count: 2" in text
    # 正文
    assert ".workflow/context/roles/executing.md: 当前 stage 角色文件" in text
    assert ".workflow/context/roles/base-role.md: 通用规约" in text


def test_snapshot_seq_increments(tmp_path):
    """req-32 / chg-03 Step 3：连续两次同 req 同 stage → 001 / 002。"""
    from harness_workflow.workflow_helpers import _write_task_context_snapshot

    root = tmp_path
    idx = [{"path": "a.md", "reason": "r1"}]
    s1 = _write_task_context_snapshot(root=root, req_id="req-99", stage="executing", index=idx)
    s2 = _write_task_context_snapshot(root=root, req_id="req-99", stage="executing", index=idx)
    assert s1.name == "executing-001.md"
    assert s2.name == "executing-002.md"


def test_snapshot_different_stage_seq_independent(tmp_path):
    """req-32 / chg-03 Step 3：不同 stage 各自从 001 起。"""
    from harness_workflow.workflow_helpers import _write_task_context_snapshot

    root = tmp_path
    idx = [{"path": "a.md", "reason": "r"}]
    s_exec = _write_task_context_snapshot(root=root, req_id="req-99", stage="executing", index=idx)
    s_test = _write_task_context_snapshot(root=root, req_id="req-99", stage="testing", index=idx)
    assert s_exec.name == "executing-001.md"
    assert s_test.name == "testing-001.md"
