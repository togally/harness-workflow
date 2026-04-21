"""Tests for req-30（slug 沟通可读性增强：全链路透出 title）chg-01（state schema — title 冗余字段）.

验证：
- runtime.yaml schema 具备 `*_title` 三字段位（AC-05）
- `_resolve_title_for_id` helper 的行为（lookup + fallback 空串）
- 写入 `current_requirement` / `current_regression` / `locked_requirement` 时 title 同步刷新（AC-06）
- `create_requirement` / `create_bugfix` 空 title 抛错
- 向后兼容：旧 runtime.yaml 无 `*_title` 字段时读出空串不炸
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import (
    DEFAULT_STATE_RUNTIME,
    STATE_RUNTIME_PATH,
    _resolve_title_for_id,
    create_bugfix,
    create_requirement,
    load_requirement_runtime,
    load_simple_yaml,
    save_requirement_runtime,
    save_simple_yaml,
)


def _init_repo(root: Path) -> None:
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True, exist_ok=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True, exist_ok=True)
    (root / ".codex" / "harness").mkdir(parents=True, exist_ok=True)
    # ensure_config writes config.json on demand; leave it default


class TestRuntimeSchemaHasTitleFields:
    def test_default_state_runtime_contains_title_fields(self) -> None:
        """AC-05：DEFAULT_STATE_RUNTIME 必须含三个 *_title 字段，默认空串。"""
        assert "current_requirement_title" in DEFAULT_STATE_RUNTIME
        assert "current_regression_title" in DEFAULT_STATE_RUNTIME
        assert "locked_requirement_title" in DEFAULT_STATE_RUNTIME
        assert DEFAULT_STATE_RUNTIME["current_requirement_title"] == ""
        assert DEFAULT_STATE_RUNTIME["current_regression_title"] == ""
        assert DEFAULT_STATE_RUNTIME["locked_requirement_title"] == ""

    def test_runtime_yaml_preserves_title_fields(self, tmp_path: Path) -> None:
        """save → load 往返，三个 *_title 不丢。"""
        _init_repo(tmp_path)
        runtime = dict(DEFAULT_STATE_RUNTIME)
        runtime["current_requirement"] = "req-30"
        runtime["current_requirement_title"] = "slug 沟通可读性增强：全链路透出 title"
        runtime["current_regression"] = "reg-01"
        runtime["current_regression_title"] = "回归示例"
        runtime["locked_requirement"] = "req-30"
        runtime["locked_requirement_title"] = "slug 沟通可读性增强：全链路透出 title"

        save_requirement_runtime(tmp_path, runtime)
        loaded = load_requirement_runtime(tmp_path)

        assert loaded["current_requirement_title"] == "slug 沟通可读性增强：全链路透出 title"
        assert loaded["current_regression_title"] == "回归示例"
        assert loaded["locked_requirement_title"] == "slug 沟通可读性增强：全链路透出 title"

    def test_backward_compat_legacy_runtime_without_title_fields(self, tmp_path: Path) -> None:
        """向后兼容：旧 runtime.yaml 缺 *_title 字段时，load 返回空串不炸。"""
        _init_repo(tmp_path)
        runtime_path = tmp_path / STATE_RUNTIME_PATH
        runtime_path.parent.mkdir(parents=True, exist_ok=True)
        # 模拟旧 runtime.yaml：无 *_title 字段
        runtime_path.write_text(
            "operation_type: requirement\n"
            "operation_target: req-legacy\n"
            "current_requirement: req-legacy\n"
            "stage: executing\n"
            "conversation_mode: open\n"
            "locked_requirement: \"\"\n"
            "locked_stage: \"\"\n"
            "current_regression: \"\"\n"
            "ff_mode: false\n"
            "ff_stage_history: []\n"
            "active_requirements:\n"
            "  - req-legacy\n",
            encoding="utf-8",
        )

        loaded = load_requirement_runtime(tmp_path)

        # 缺失字段回填为空串
        assert loaded.get("current_requirement_title", "") == ""
        assert loaded.get("current_regression_title", "") == ""
        assert loaded.get("locked_requirement_title", "") == ""


class TestResolveTitleForId:
    def test_resolve_title_for_req_returns_state_title(self, tmp_path: Path) -> None:
        """req-* 前缀 → 读 state/requirements/*.yaml 的 title 字段。"""
        _init_repo(tmp_path)
        state_file = tmp_path / ".workflow" / "state" / "requirements" / "req-99-demo.yaml"
        save_simple_yaml(
            state_file,
            {"id": "req-99", "title": "示例 demo 需求", "stage": "executing"},
            ordered_keys=["id", "title", "stage"],
        )

        title = _resolve_title_for_id(tmp_path, "req-99")
        assert title == "示例 demo 需求"

    def test_resolve_title_for_bugfix_returns_state_title(self, tmp_path: Path) -> None:
        """bugfix-* 前缀 → 读 state/bugfixes/*.yaml 的 title 字段。"""
        _init_repo(tmp_path)
        state_file = tmp_path / ".workflow" / "state" / "bugfixes" / "bugfix-9-demo.yaml"
        save_simple_yaml(
            state_file,
            {"id": "bugfix-9", "title": "示例 bugfix 标题", "stage": "regression"},
            ordered_keys=["id", "title", "stage"],
        )

        title = _resolve_title_for_id(tmp_path, "bugfix-9")
        assert title == "示例 bugfix 标题"

    def test_resolve_title_missing_returns_empty(self, tmp_path: Path) -> None:
        """找不到 id 对应文件时返回空串，不抛错。"""
        _init_repo(tmp_path)
        title = _resolve_title_for_id(tmp_path, "req-404")
        assert title == ""

    def test_resolve_title_for_regression_returns_empty(self, tmp_path: Path) -> None:
        """reg-* 无独立 state yaml，返回空串，不抛错。"""
        _init_repo(tmp_path)
        title = _resolve_title_for_id(tmp_path, "reg-01")
        assert title == ""

    def test_resolve_title_unknown_prefix_returns_empty(self, tmp_path: Path) -> None:
        """未知前缀 → 返回空串不抛错。"""
        _init_repo(tmp_path)
        assert _resolve_title_for_id(tmp_path, "unknown-1") == ""
        assert _resolve_title_for_id(tmp_path, "") == ""


class TestTitleSyncOnRuntimeWrite:
    def test_create_requirement_syncs_title_to_runtime(self, tmp_path: Path) -> None:
        """create_requirement 写入 current_requirement 时同步写 current_requirement_title。"""
        _init_repo(tmp_path)
        create_requirement(tmp_path, "同步标题 demo", requirement_id="req-99")

        runtime = load_simple_yaml(tmp_path / STATE_RUNTIME_PATH)
        assert runtime.get("current_requirement") == "req-99"
        assert runtime.get("current_requirement_title") == "同步标题 demo"

    def test_create_bugfix_syncs_title_to_runtime(self, tmp_path: Path) -> None:
        """create_bugfix 写入 current_requirement 时同步写 current_requirement_title。"""
        _init_repo(tmp_path)
        create_bugfix(tmp_path, "同步 bugfix 标题", bugfix_id="bugfix-9")

        runtime = load_simple_yaml(tmp_path / STATE_RUNTIME_PATH)
        assert runtime.get("current_requirement") == "bugfix-9"
        assert runtime.get("current_requirement_title") == "同步 bugfix 标题"

    def test_create_requirement_requires_nonempty_title(self, tmp_path: Path) -> None:
        """传空 title 时 create_requirement 抛 SystemExit。"""
        _init_repo(tmp_path)
        with pytest.raises(SystemExit):
            create_requirement(tmp_path, "   ", requirement_id="req-99")

    def test_create_bugfix_requires_nonempty_title(self, tmp_path: Path) -> None:
        """传空 title 时 create_bugfix 抛 SystemExit。"""
        _init_repo(tmp_path)
        with pytest.raises(SystemExit):
            create_bugfix(tmp_path, "", bugfix_id="bugfix-9")
