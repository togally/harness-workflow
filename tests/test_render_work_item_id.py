"""Tests for req-30（slug 沟通可读性增强：全链路透出 title）chg-02（CLI 渲染 — render_work_item_id helper）.

覆盖 AC-03 / AC-04 / AC-06 / AC-09：
- runtime 缓存优先命中：`render_work_item_id` 读 `runtime["*_title"]`
- state fallback：runtime miss 时读 `state/requirements/*.yaml`
- 缺失降级：runtime + state 都拿不到 → 返回 ``{id} (no title)``
- 空 id：返回 ``"(none)"``
- sug 文件读 frontmatter title
- `workflow_status` 集成 smoke：stdout 打印带 title

req-31（批量建议合集（20条））/ chg-05（legacy yaml strip 兜底）/ Step 1（sug-23）新增：
- legacy yaml 脏数据 title（前后空格 / 包围引号）→ render 时自动 strip。
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import (
    DEFAULT_STATE_RUNTIME,
    STATE_RUNTIME_PATH,
    render_work_item_id,
    save_requirement_runtime,
    save_simple_yaml,
    workflow_status,
)


def _init_repo(root: Path) -> None:
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True, exist_ok=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True, exist_ok=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True, exist_ok=True)
    (root / ".codex" / "harness").mkdir(parents=True, exist_ok=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class TestRenderWorkItemIdCoreBranches:
    def test_render_with_runtime_cache(self, tmp_path: Path) -> None:
        """runtime 缓存命中 → 返回 `{id}（{title}）`。"""
        _init_repo(tmp_path)
        runtime = dict(DEFAULT_STATE_RUNTIME)
        runtime["current_requirement"] = "req-30"
        runtime["current_requirement_title"] = "slug 沟通可读性增强：全链路透出 title"

        rendered = render_work_item_id("req-30", runtime=runtime, root=tmp_path)
        assert rendered == "req-30（slug 沟通可读性增强：全链路透出 title）"

    def test_render_with_state_fallback(self, tmp_path: Path) -> None:
        """runtime 缓存空 → fallback 到 state/requirements/*.yaml。"""
        _init_repo(tmp_path)
        state_file = tmp_path / ".workflow" / "state" / "requirements" / "req-99-demo.yaml"
        save_simple_yaml(
            state_file,
            {"id": "req-99", "title": "demo 标题", "stage": "executing"},
            ordered_keys=["id", "title", "stage"],
        )

        rendered = render_work_item_id("req-99", runtime=None, root=tmp_path)
        assert rendered == "req-99（demo 标题）"

    def test_render_missing_title_fallback(self, tmp_path: Path) -> None:
        """runtime + state 都拿不到 → 返回 `{id} (no title)` 不抛错。"""
        _init_repo(tmp_path)
        rendered = render_work_item_id("req-404", runtime=None, root=tmp_path)
        assert rendered == "req-404 (no title)"

    def test_render_empty_id_returns_none_placeholder(self, tmp_path: Path) -> None:
        """空 id → 返回 `(none)`，与 workflow_status 旧行为一致。"""
        _init_repo(tmp_path)
        assert render_work_item_id("", runtime=None, root=tmp_path) == "(none)"
        assert render_work_item_id("   ", runtime=None, root=tmp_path) == "(none)"

    def test_render_runtime_cache_priority_over_state(self, tmp_path: Path) -> None:
        """runtime 缓存优先于 state yaml（O(1) cache 命中）。"""
        _init_repo(tmp_path)
        # state 里是 "state 值"，runtime 缓存是 "cache 值"
        state_file = tmp_path / ".workflow" / "state" / "requirements" / "req-77-x.yaml"
        save_simple_yaml(
            state_file,
            {"id": "req-77", "title": "state 值", "stage": "executing"},
            ordered_keys=["id", "title", "stage"],
        )
        runtime = dict(DEFAULT_STATE_RUNTIME)
        runtime["current_requirement"] = "req-77"
        runtime["current_requirement_title"] = "cache 值"

        rendered = render_work_item_id("req-77", runtime=runtime, root=tmp_path)
        assert rendered == "req-77（cache 值）"

    def test_render_bugfix_state_fallback(self, tmp_path: Path) -> None:
        """bugfix-* → 读 state/bugfixes/*.yaml。"""
        _init_repo(tmp_path)
        state_file = tmp_path / ".workflow" / "state" / "bugfixes" / "bugfix-9-x.yaml"
        save_simple_yaml(
            state_file,
            {"id": "bugfix-9", "title": "bugfix 演示", "stage": "regression"},
            ordered_keys=["id", "title", "stage"],
        )

        rendered = render_work_item_id("bugfix-9", runtime=None, root=tmp_path)
        assert rendered == "bugfix-9（bugfix 演示）"


class TestRenderSuggestion:
    def test_render_suggestion_reads_frontmatter_title(self, tmp_path: Path) -> None:
        """sug-* → 读 sug 文件 frontmatter 的 `title:` 字段。"""
        _init_repo(tmp_path)
        sug_path = tmp_path / ".workflow" / "flow" / "suggestions" / "sug-99-demo.md"
        sug_path.write_text(
            "---\n"
            "id: sug-99\n"
            'title: "示例建议 title"\n'
            "status: pending\n"
            "created_at: 2026-04-21\n"
            "priority: medium\n"
            "---\n\n"
            "body line 1\n",
            encoding="utf-8",
        )

        rendered = render_work_item_id("sug-99", runtime=None, root=tmp_path)
        assert rendered == "sug-99（示例建议 title）"

    def test_render_suggestion_falls_back_to_body_first_line(self, tmp_path: Path) -> None:
        """无 frontmatter.title → 降级读 body 首行（≤40 字符）。"""
        _init_repo(tmp_path)
        sug_path = tmp_path / ".workflow" / "flow" / "suggestions" / "sug-88-legacy.md"
        sug_path.write_text(
            "legacy suggestion body first line\nsecond line ignored\n",
            encoding="utf-8",
        )

        rendered = render_work_item_id("sug-88", runtime=None, root=tmp_path)
        # body 首行被截取作为 title
        assert rendered.startswith("sug-88（")
        assert "legacy suggestion body first line" in rendered

    def test_render_suggestion_missing_file(self, tmp_path: Path) -> None:
        """sug 文件不存在 → `(no title)` 降级。"""
        _init_repo(tmp_path)
        rendered = render_work_item_id("sug-404", runtime=None, root=tmp_path)
        assert rendered == "sug-404 (no title)"


class TestWorkflowStatusPrintsTitle:
    def test_workflow_status_prints_current_requirement_with_title(self, tmp_path: Path) -> None:
        """AC-03 集成 smoke：`workflow_status` stdout 的 `current_requirement:` 行同行带 title。"""
        _init_repo(tmp_path)
        state_file = tmp_path / ".workflow" / "state" / "requirements" / "req-30-x.yaml"
        save_simple_yaml(
            state_file,
            {"id": "req-30", "title": "slug 沟通可读性增强：全链路透出 title", "stage": "executing"},
            ordered_keys=["id", "title", "stage"],
        )
        runtime = dict(DEFAULT_STATE_RUNTIME)
        runtime["current_requirement"] = "req-30"
        runtime["current_requirement_title"] = "slug 沟通可读性增强：全链路透出 title"
        runtime["active_requirements"] = ["req-30"]
        save_requirement_runtime(tmp_path, runtime)

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = workflow_status(tmp_path)
        assert rc == 0
        output = buf.getvalue()

        # 首行同行附带 title
        assert "current_requirement: req-30（slug 沟通可读性增强：全链路透出 title）" in output
        # active_requirements 行也渲染带 title
        assert "active_requirements: req-30（slug 沟通可读性增强：全链路透出 title）" in output

    def test_workflow_status_fallback_when_title_cache_empty(self, tmp_path: Path) -> None:
        """AC-04：runtime 缓存为空时 fallback 到 state yaml 读 title。"""
        _init_repo(tmp_path)
        state_file = tmp_path / ".workflow" / "state" / "requirements" / "req-30-x.yaml"
        save_simple_yaml(
            state_file,
            {"id": "req-30", "title": "fallback title", "stage": "executing"},
            ordered_keys=["id", "title", "stage"],
        )
        runtime = dict(DEFAULT_STATE_RUNTIME)
        runtime["current_requirement"] = "req-30"
        # 故意留空 cache
        runtime["current_requirement_title"] = ""
        runtime["active_requirements"] = ["req-30"]
        save_requirement_runtime(tmp_path, runtime)

        buf = io.StringIO()
        with redirect_stdout(buf):
            workflow_status(tmp_path)
        output = buf.getvalue()

        # state fallback 命中
        assert "req-30（fallback title）" in output

    def test_workflow_status_empty_id_renders_none(self, tmp_path: Path) -> None:
        """AC-04：无 current_requirement 时打印 `(none)` 不抛错。"""
        _init_repo(tmp_path)
        runtime = dict(DEFAULT_STATE_RUNTIME)
        save_requirement_runtime(tmp_path, runtime)

        buf = io.StringIO()
        with redirect_stdout(buf):
            workflow_status(tmp_path)
        output = buf.getvalue()

        assert "current_requirement: (none)" in output


class TestRenderWorkItemIdLegacyYamlStrip:
    """req-31（批量建议合集（20条））/ chg-05（legacy yaml strip 兜底）/ Step 1（sug-23）：
    legacy yaml 脏数据（title 前后空格 / 包围引号）render 时 strip 兜底。
    """

    def test_render_strips_leading_trailing_whitespace_from_runtime(self, tmp_path: Path) -> None:
        """runtime 缓存内 title 前后有空格 → render 结果不含空格。"""
        _init_repo(tmp_path)
        runtime = dict(DEFAULT_STATE_RUNTIME)
        runtime["current_requirement"] = "req-77"
        runtime["current_requirement_title"] = "  dirty title  "
        rendered = render_work_item_id("req-77", runtime=runtime, root=tmp_path)
        assert rendered == "req-77（dirty title）"

    def test_render_strips_single_quotes_from_state(self, tmp_path: Path) -> None:
        """state yaml 内 title 被外层单引号包围 → render 结果去掉外层单引号。"""
        _init_repo(tmp_path)
        state_file = tmp_path / ".workflow" / "state" / "requirements" / "req-78-x.yaml"
        # 故意写入脏数据形式（title 值包含外层单引号）
        state_file.write_text(
            "\n".join([
                'id: "req-78"',
                "title: \"'批量建议合集'\"",
                'stage: "executing"',
                "",
            ]),
            encoding="utf-8",
        )
        rendered = render_work_item_id("req-78", runtime=None, root=tmp_path)
        assert rendered == "req-78（批量建议合集）"

    def test_render_strips_double_quotes(self, tmp_path: Path) -> None:
        _init_repo(tmp_path)
        runtime = dict(DEFAULT_STATE_RUNTIME)
        runtime["current_requirement"] = "req-79"
        runtime["current_requirement_title"] = '"foo"'
        rendered = render_work_item_id("req-79", runtime=runtime, root=tmp_path)
        assert rendered == "req-79（foo）"

    def test_render_handles_nested_quotes_and_spaces(self, tmp_path: Path) -> None:
        _init_repo(tmp_path)
        runtime = dict(DEFAULT_STATE_RUNTIME)
        runtime["current_requirement"] = "req-80"
        runtime["current_requirement_title"] = ' "批量建议合集" '
        rendered = render_work_item_id("req-80", runtime=runtime, root=tmp_path)
        assert rendered == "req-80（批量建议合集）"

    def test_render_preserves_internal_quotes(self, tmp_path: Path) -> None:
        """内部（非首尾）单引号不被误去，避免误改合法字符。"""
        _init_repo(tmp_path)
        runtime = dict(DEFAULT_STATE_RUNTIME)
        runtime["current_requirement"] = "req-81"
        runtime["current_requirement_title"] = "foo's bar"
        rendered = render_work_item_id("req-81", runtime=runtime, root=tmp_path)
        assert rendered == "req-81（foo's bar）"
