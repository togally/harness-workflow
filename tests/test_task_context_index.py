"""req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）

覆盖 AC-03 / AC-04 / AC-07：
- `_build_subagent_briefing` 扩展 task_context_index / task_context_index_file 字段
- `_build_task_context_index` helper：默认集 + 上限 8 + profile 加权 + stderr warn
- `_write_task_context_snapshot` 落盘：frontmatter 四字段 + 正文 + seq 递增
- `_resolve_task_context_paths`：fallback 语义（路径不存在不报错）
- 集成：harness next --execute stdout 含 fence + 快照落盘
"""

from __future__ import annotations

import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Step 1：briefing 扩展基础字段
# ---------------------------------------------------------------------------


def _extract_briefing_json(text: str) -> dict:
    """从 subagent briefing fence 中抽取 JSON 并 loads。"""
    match = re.search(r"```subagent-briefing\n(\{.*?\})\n```", text, flags=re.DOTALL)
    assert match is not None, f"未找到 briefing fence: {text!r}"
    return json.loads(match.group(1))


def test_briefing_contains_task_context_index():
    """req-32 / chg-03 Step 1：briefing 带 task_context_index 字段，可被 json.loads 解析。"""
    from harness_workflow.workflow_helpers import _build_subagent_briefing

    index = [
        {"path": ".workflow/context/roles/executing.md", "reason": "当前 stage 角色文件"},
        {"path": ".workflow/context/roles/base-role.md", "reason": "通用规约"},
    ]
    text = _build_subagent_briefing(
        "executing",
        "req-99",
        "测试需求",
        task_context_index=index,
        task_context_index_file=".workflow/state/sessions/req-99/task-context/executing-001.md",
    )
    payload = _extract_briefing_json(text)
    assert payload["task_context_index"] == index
    assert payload["task_context_index_file"] == ".workflow/state/sessions/req-99/task-context/executing-001.md"


def test_briefing_backward_compatible_without_index():
    """req-32 / chg-03 Step 1：未传 index 时 briefing 不应新增字段（向后兼容既有测试基线）。"""
    from harness_workflow.workflow_helpers import _build_subagent_briefing

    text = _build_subagent_briefing("executing", "req-99", "测试需求")
    payload = _extract_briefing_json(text)
    # 未传 index/索引文件时字段缺省（不强制存在）
    assert payload.get("task_context_index", []) == []
    assert payload.get("task_context_index_file", "") == ""


# ---------------------------------------------------------------------------
# Step 2：_build_task_context_index helper
# ---------------------------------------------------------------------------


def _mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _touch(p: Path, text: str = "") -> None:
    _mkdir(p.parent)
    p.write_text(text, encoding="utf-8")


def test_build_index_basic_stage_defaults(tmp_path):
    """req-32 / chg-03 Step 2：profile 缺失 → 基础默认集（role + stage-role + base-role）。"""
    from harness_workflow.workflow_helpers import _build_task_context_index

    root = tmp_path
    _touch(root / ".workflow/context/roles/executing.md")
    _touch(root / ".workflow/context/roles/stage-role.md")
    _touch(root / ".workflow/context/roles/base-role.md")

    index = _build_task_context_index(root=root, stage="executing", req_id="req-99")
    paths = [item["path"] for item in index]
    assert ".workflow/context/roles/executing.md" in paths
    assert ".workflow/context/roles/stage-role.md" in paths
    assert ".workflow/context/roles/base-role.md" in paths
    # 每条都有 reason
    for item in index:
        assert item.get("reason"), f"missing reason: {item}"


def test_build_index_truncates_above_8(tmp_path, capsys):
    """req-32 / chg-03 Step 2：候选 > 8 时截断到 8 + stderr warn。"""
    from harness_workflow.workflow_helpers import _build_task_context_index

    root = tmp_path
    # 构造超量候选：默认集 + 所有 experience/role/constraint + checklist
    _touch(root / ".workflow/context/roles/executing.md")
    _touch(root / ".workflow/context/roles/stage-role.md")
    _touch(root / ".workflow/context/roles/base-role.md")
    _touch(root / ".workflow/context/experience/roles/executing.md")
    _touch(root / ".workflow/context/experience/stage/executing.md")
    _touch(root / ".workflow/constraints/risk.md")
    _touch(root / ".workflow/constraints/boundaries.md")
    _touch(root / ".workflow/constraints/recovery.md")
    _touch(root / ".workflow/context/checklists/review-checklist.md")
    _touch(root / ".workflow/context/checklists/role-inheritance-checklist.md")
    # profile 存在会再追加一条
    _touch(root / ".workflow/context/project-profile.md", "---\nschema: project-profile/v1\n---\n## 结构化字段\n- language: python\n")

    index = _build_task_context_index(root=root, stage="executing", req_id="req-99")
    assert len(index) <= 8, f"索引超过 8 条: {len(index)}"
    captured = capsys.readouterr()
    assert "task_context_index" in captured.err and "truncated" in captured.err


def test_build_index_reads_project_profile_when_present(tmp_path):
    """req-32 / chg-03 Step 2：profile 存在 → 索引含 project-profile.md；缺失时不含。"""
    from harness_workflow.workflow_helpers import _build_task_context_index

    root = tmp_path
    _touch(root / ".workflow/context/roles/executing.md")
    _touch(root / ".workflow/context/roles/stage-role.md")
    _touch(root / ".workflow/context/roles/base-role.md")

    # 缺失 profile
    idx_missing = _build_task_context_index(root=root, stage="executing", req_id="req-99")
    assert not any(item["path"].endswith("project-profile.md") for item in idx_missing)

    # 补一个 profile
    _touch(
        root / ".workflow/context/project-profile.md",
        "---\nschema: project-profile/v1\n---\n## 结构化字段\n- language: python\n- stack_tags:\n  - python+pyproject\n",
    )
    idx_present = _build_task_context_index(root=root, stage="executing", req_id="req-99")
    assert any(item["path"].endswith("project-profile.md") for item in idx_present)


# ---------------------------------------------------------------------------
# Step 5：_resolve_task_context_paths helper（C2 回退语义）
# ---------------------------------------------------------------------------


def test_resolve_task_context_paths_missing_not_raise(tmp_path):
    """req-32 / chg-03 Step 5 / AC-04：路径不存在 → 返回 (existing, missing) 分流，不报错。"""
    from harness_workflow.workflow_helpers import _resolve_task_context_paths

    root = tmp_path
    _touch(root / ".workflow/context/roles/executing.md")
    index = [
        {"path": ".workflow/context/roles/executing.md", "reason": "exists"},
        {"path": ".workflow/context/does-not-exist.md", "reason": "missing"},
    ]
    existing, missing = _resolve_task_context_paths(index, root)
    assert any(p.endswith("executing.md") for p in existing)
    assert any(p.endswith("does-not-exist.md") for p in missing)


# ---------------------------------------------------------------------------
# Step 4：集成 —— workflow_next(execute=True) 端到端
# ---------------------------------------------------------------------------


def _bootstrap_tmp_root(tmp_path: Path, stage: str = "planning", req_id: str = "req-99") -> Path:  # P-1 default-pick C（req-31 chg-01）：planning 替代 changes_review
    """构造最小可用的 workflow tmp root：runtime.yaml + 一个 requirement state yaml。"""
    import yaml as _yaml

    root = tmp_path
    (root / ".workflow/state/requirements").mkdir(parents=True, exist_ok=True)
    (root / ".workflow/state/sessions").mkdir(parents=True, exist_ok=True)
    (root / ".workflow/context/roles").mkdir(parents=True, exist_ok=True)

    # 默认集文件
    _touch(root / ".workflow/context/roles/executing.md")
    _touch(root / ".workflow/context/roles/planning.md")
    _touch(root / ".workflow/context/roles/stage-role.md")
    _touch(root / ".workflow/context/roles/base-role.md")

    # runtime.yaml
    runtime = {
        "operation_type": "requirement",
        "operation_target": req_id,
        "current_requirement": req_id,
        "current_requirement_title": "测试需求",
        "stage": stage,
        "conversation_mode": "open",
        "ff_mode": False,
        "active_requirements": [req_id],
    }
    (root / ".workflow/state/runtime.yaml").write_text(_yaml.safe_dump(runtime, allow_unicode=True), encoding="utf-8")

    # state/requirements/{req_id}.yaml
    state = {"id": req_id, "title": "测试需求", "stage": stage, "status": "active"}
    (root / f".workflow/state/requirements/{req_id}.yaml").write_text(
        _yaml.safe_dump(state, allow_unicode=True), encoding="utf-8"
    )
    return root


def test_next_execute_emits_briefing_with_index(tmp_path, capsys):
    """req-32 / chg-03 Step 4 / AC-03 + AC-07：`next --execute` stdout 含 task_context_index + task_context_index_file；快照落盘。"""
    from harness_workflow.workflow_helpers import workflow_next

    # ready_for_execution → executing 是会派发 briefing 的路径；planning → ready_for_execution
    # 属于 _NO_BRIEFING_STAGES，不触发索引构建。（P-1 default-pick C, req-31 chg-01）
    root = _bootstrap_tmp_root(tmp_path, stage="ready_for_execution", req_id="req-99")

    rc = workflow_next(root, execute=True)
    assert rc == 0

    captured = capsys.readouterr()
    payload = _extract_briefing_json(captured.out)
    assert "task_context_index" in payload
    assert isinstance(payload["task_context_index"], list)
    assert "task_context_index_file" in payload
    snapshot_rel = payload["task_context_index_file"]
    assert snapshot_rel, "快照文件相对路径不应为空"
    snapshot_abs = root / snapshot_rel
    assert snapshot_abs.exists(), f"快照未落盘: {snapshot_abs}"
    text = snapshot_abs.read_text(encoding="utf-8")
    # frontmatter 四字段
    assert "req_id:" in text
    assert "stage:" in text
    assert "ts:" in text
    assert "index_count:" in text
    # 正文每行 {path}: {reason}
    for item in payload["task_context_index"]:
        assert f"{item['path']}: {item['reason']}" in text
