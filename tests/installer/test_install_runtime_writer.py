"""Unit and integration tests for bugfix-11: install runtime.yaml writer 3 bugs.

bugfix-11: install runtime.yaml 反写 3 bug:
  B1 - 多重 quote 累积（pyyaml + simple_yaml round-trip 不闭合）
  B2 - gstack_status 字段消失（ordered_keys 白名单缺失）
  B3 - active_requirements 清空（load_simple_yaml 不兼容 pyyaml block-seq 0 缩进）

修复方案 B: 统一 runtime.yaml writer，所有写盘走 save_requirement_runtime。
用户拍板：_parse_simple_yaml_scalar 加 self-heal 剥多重单引号层。

Tests (10 cases):
  P0 (6 cases):
    TC-01  test_render_yaml_scalar_quoted_string_no_double_escape
    TC-02  test_render_yaml_scalar_empty_string_no_quote_accumulation
    TC-03  test_render_yaml_scalar_iso_datetime_no_quote_accumulation
    TC-04  test_save_requirement_runtime_preserves_gstack_status
    TC-05  test_save_requirement_runtime_preserves_gstack_run_log
    TC-06  test_load_simple_yaml_preserves_active_requirements_after_pyyaml_write
  P1 (4 cases):
    TC-07  test_install_agent_writes_gstack_status_to_runtime_yaml
    TC-08  test_install_agent_idempotent_runtime_yaml (3 rounds)
    TC-09  test_parse_simple_yaml_scalar_self_heal_multiple_quotes
    TC-10  test_install_agent_active_requirements_preserved
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow import workflow_helpers as wh  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_clean_runtime(path: Path, active_requirements: list[str] | None = None) -> None:
    """Write a clean (non-polluted) runtime.yaml for testing."""
    if active_requirements is None:
        active_requirements = ["req-54"]
    ar_lines = "\n".join(f"  - {r}" for r in active_requirements)
    path.write_text(
        "operation_type: \"requirement\"\n"
        "operation_target: \"req-54\"\n"
        "current_requirement: \"req-54\"\n"
        "current_requirement_title: \"test req\"\n"
        "stage: \"executing\"\n"
        "stage_entered_at: \"2026-05-08T03:30:00.000000+00:00\"\n"
        "conversation_mode: \"open\"\n"
        "locked_requirement: \"\"\n"
        "locked_requirement_title: \"\"\n"
        "locked_stage: \"\"\n"
        "current_regression: \"\"\n"
        "current_regression_title: \"\"\n"
        "ff_mode: false\n"
        "ff_stage_history: []\n"
        f"active_requirements:\n{ar_lines}\n",
        encoding="utf-8",
    )


def _make_project(tmp_path: Path, active_requirements: list[str] | None = None) -> Path:
    """Create a minimal project directory with clean runtime.yaml."""
    project = tmp_path / "project"
    state_dir = project / ".workflow" / "state"
    state_dir.mkdir(parents=True)
    _write_clean_runtime(state_dir / "runtime.yaml", active_requirements)
    return project


# ---------------------------------------------------------------------------
# TC-01  test_render_yaml_scalar_quoted_string_no_double_escape  (B1 P0)
# ---------------------------------------------------------------------------

def test_render_yaml_scalar_quoted_string_no_double_escape() -> None:
    """_render_yaml_scalar 对已经是 clean 字符串不应产生内嵌单引号。

    B1 root: pyyaml 写出 '2026-05-08T03:30:00.000000+00:00'，simple_yaml 不剥单引号，
    _render_yaml_scalar 用 json.dumps 包双引号后得到
    "\"'2026-05-08T03:30:00.000000+00:00'\""，含字面单引号字符。

    修复后: 干净字符串 round-trip 不应含字面单引号字符。
    """
    ts = "2026-05-08T03:30:00.000000+00:00"
    rendered = wh._render_yaml_scalar(ts)
    # 应当是标准 JSON 双引号包裹，无内嵌字面单引号
    assert rendered == f'"{ts}"', f"Expected clean quoted scalar, got: {rendered!r}"
    assert "'" not in rendered, f"Unexpected literal single-quote in rendered scalar: {rendered!r}"


# ---------------------------------------------------------------------------
# TC-02  test_render_yaml_scalar_empty_string_no_quote_accumulation  (B1 P0)
# ---------------------------------------------------------------------------

def test_render_yaml_scalar_empty_string_no_quote_accumulation() -> None:
    """空字符串 round-trip: _render_yaml_scalar("") → load → scalar 仍为空字符串。

    B1 root: pyyaml 把空串写成 ''（字面两单引号），simple_yaml 不剥，load 得到含两单引号
    字符的字符串 "''"，再 _render_yaml_scalar 得到 "\"''\"" → 下次 pyyaml 读出
    4 字面单引号 → 循环积累。
    """
    empty_rendered = wh._render_yaml_scalar("")
    # 写出的形态应当是标准 json ""（两个双引号），不含单引号
    assert empty_rendered == '""', f"Expected '\"\"', got: {empty_rendered!r}"
    # 再 parse 回来应为空字符串
    parsed = wh._parse_simple_yaml_scalar(empty_rendered)
    assert parsed == "", f"Expected empty string after round-trip, got: {parsed!r}"


# ---------------------------------------------------------------------------
# TC-03  test_render_yaml_scalar_iso_datetime_no_quote_accumulation  (B1 P0)
# ---------------------------------------------------------------------------

def test_render_yaml_scalar_iso_datetime_no_quote_accumulation() -> None:
    """ISO 时间戳 round-trip: render → parse 还原，不累积引号层。"""
    ts = "2026-05-08T03:30:00.000000+00:00"
    rendered = wh._render_yaml_scalar(ts)
    parsed = wh._parse_simple_yaml_scalar(rendered)
    assert parsed == ts, (
        f"ISO datetime round-trip failed: rendered={rendered!r}, parsed={parsed!r}"
    )
    # 无单引号字面字符
    assert "'" not in str(parsed), f"Literal single-quote in parsed value: {parsed!r}"


# ---------------------------------------------------------------------------
# TC-04  test_save_requirement_runtime_preserves_gstack_status  (B2 P0)
# ---------------------------------------------------------------------------

def test_save_requirement_runtime_preserves_gstack_status(tmp_path: Path) -> None:
    """save_requirement_runtime 不应裁剪 gstack_status 字段（B2）。

    B2 root: ordered_keys 白名单缺 gstack_status，save_simple_yaml 遍历 ordered_keys
    时静默跳过该字段，导致写后 runtime.yaml 无 gstack_status 段。
    """
    project = _make_project(tmp_path)
    runtime = wh.load_requirement_runtime(project)
    runtime["gstack_status"] = {
        "installed_skills": ["office-hours", "qa"],
        "vendor_version": "abc1234",
        "last_install": "2026-05-08T00:00:00+00:00",
        "agent_kind_compatible": True,
    }
    wh.save_requirement_runtime(project, runtime)

    # Reload and check
    loaded = wh.load_requirement_runtime(project)
    assert "gstack_status" in loaded, "gstack_status 字段在 save 后消失（B2 未修复）"
    gs = loaded["gstack_status"]
    assert isinstance(gs, dict), f"gstack_status 应为 dict，实际: {type(gs)}"
    assert gs.get("vendor_version") == "abc1234"
    assert gs.get("agent_kind_compatible") is True


# ---------------------------------------------------------------------------
# TC-05  test_save_requirement_runtime_preserves_gstack_run_log  (B2 P0)
# ---------------------------------------------------------------------------

def test_save_requirement_runtime_preserves_gstack_run_log(tmp_path: Path) -> None:
    """save_requirement_runtime 不应裁剪 gstack_run_log 字段（B2）。"""
    project = _make_project(tmp_path)
    runtime = wh.load_requirement_runtime(project)
    runtime["gstack_run_log"] = ["error: failed to copy investigate/SKILL.md"]
    wh.save_requirement_runtime(project, runtime)

    loaded = wh.load_requirement_runtime(project)
    assert "gstack_run_log" in loaded, "gstack_run_log 字段在 save 后消失（B2 未修复）"
    run_log = loaded["gstack_run_log"]
    assert isinstance(run_log, list), f"gstack_run_log 应为 list，实际: {type(run_log)}"
    assert len(run_log) == 1
    assert "investigate" in run_log[0]


# ---------------------------------------------------------------------------
# TC-06  test_load_simple_yaml_preserves_active_requirements_after_pyyaml_write  (B3 P0)
# ---------------------------------------------------------------------------

def test_load_simple_yaml_preserves_active_requirements_after_pyyaml_write(tmp_path: Path) -> None:
    """load_simple_yaml 应兼容 pyyaml block-seq 0 缩进格式（B3）。

    B3 root: pyyaml 默认 block-seq 输出：
      active_requirements:
      - req-X
    load_simple_yaml 判定 `indent > collection_indent`（两者均为 0），条件不成立，
    dash 行被当作顶层 key（无冒号被 continue 跳过）→ active_requirements 变 []。
    修复后 `indent >= collection_indent` 应正确识别 0 缩进 dash 行。
    """
    yaml_file = tmp_path / "runtime.yaml"
    # 模拟 pyyaml 写出的 0 缩进 block-seq 格式
    yaml_file.write_text(
        "operation_type: requirement\n"
        "current_requirement: req-54\n"
        "active_requirements:\n"
        "- req-54\n"
        "- req-55\n",
        encoding="utf-8",
    )
    loaded = wh.load_simple_yaml(yaml_file)
    assert loaded.get("active_requirements") == ["req-54", "req-55"], (
        f"B3 未修复：active_requirements 应为 ['req-54', 'req-55']，"
        f"实际: {loaded.get('active_requirements')!r}"
    )


# ---------------------------------------------------------------------------
# TC-07  test_install_agent_writes_gstack_status_to_runtime_yaml  (端到端 P1)
# ---------------------------------------------------------------------------

def test_install_agent_writes_gstack_status_to_runtime_yaml(tmp_path: Path) -> None:
    """install_agent (agent=claude) 完成后 runtime.yaml 应含 gstack_status 4 子字段。"""
    project = _make_project(tmp_path)

    # Build fake gstack assets
    fake_assets = tmp_path / "assets" / "gstack-skills"
    shared = fake_assets / "_shared"
    shared.mkdir(parents=True)
    (shared / "LICENSE-gstack").write_text("MIT\n")
    (shared / "VERSION-gstack").write_text(
        "upstream_url: https://example.com/gstack\ncommit: def5678\n"
        "vendor_timestamp: 2026-05-08T00:00:00Z\n"
    )
    for skill in ["office-hours", "qa"]:
        skill_dir = fake_assets / skill
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"# {skill}\n")
        (skill_dir / "VERSION-gstack").write_text(
            "upstream_url: https://example.com/gstack\ncommit: def5678\n"
        )

    target_skills = tmp_path / "claude_skills"
    target_skills.mkdir()

    with (
        patch.object(wh, "GSTACK_SKILLS_ROOT", fake_assets),
        patch.object(wh, "_project_skill_targets", return_value=[]),
        patch.object(wh, "install_local_skills", return_value=[]),
        patch.object(wh, "write_active_agent", return_value=None),
        patch("pathlib.Path.home", return_value=target_skills.parent),
    ):
        # Patch home() / ".claude" / "skills" → target_skills
        with patch.object(Path, "home", return_value=tmp_path):
            claude_skills_root = tmp_path / ".claude" / "skills"
            claude_skills_root.mkdir(parents=True, exist_ok=True)
            rc = wh.install_agent(project, "claude", force_gstack=True)

    assert rc == 0, f"install_agent returned {rc}, expected 0"

    loaded = wh.load_requirement_runtime(project)
    assert "gstack_status" in loaded, (
        "B2 端到端: install_agent 后 runtime.yaml 无 gstack_status 段"
    )
    gs = loaded["gstack_status"]
    assert isinstance(gs, dict)
    for field in ("installed_skills", "vendor_version", "last_install", "agent_kind_compatible"):
        assert field in gs, f"gstack_status 缺少字段: {field!r}"
    assert gs["agent_kind_compatible"] is True


# ---------------------------------------------------------------------------
# TC-08  test_install_agent_idempotent_runtime_yaml  (端到端 P1，连跑 3 次)
# ---------------------------------------------------------------------------

def test_install_agent_idempotent_runtime_yaml(tmp_path: Path) -> None:
    """连跑 3 次 _write_gstack_status + save_requirement_runtime，字段值不累积单引号污染。

    B1 端到端: 每轮 install 后 locked_requirement / stage_entered_at 等字段值
    不应含字面单引号字符。第 3 轮后 locked_requirement 仍为空字符串（非 "''''''"）。
    """
    project = _make_project(tmp_path)

    def _one_install_cycle() -> None:
        """模拟一次 install_agent 末尾的 _write_gstack_status 调用。"""
        status = {
            "installed_skills": ["office-hours"],
            "vendor_version": "abc1234",
            "last_install": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "agent_kind_compatible": True,
        }
        wh._write_gstack_status(project, status)

    for _ in range(3):
        _one_install_cycle()

    loaded = wh.load_requirement_runtime(project)

    # locked_requirement 应为空字符串，不含单引号
    locked_req = loaded.get("locked_requirement", "MISSING")
    assert locked_req == "", (
        f"B1 端到端: 3 轮后 locked_requirement 应为 ''，实际: {locked_req!r}"
    )

    # stage_entered_at 不应含字面单引号
    stage_at = str(loaded.get("stage_entered_at", ""))
    assert "'" not in stage_at, (
        f"B1 端到端: 3 轮后 stage_entered_at 含字面单引号: {stage_at!r}"
    )

    # gstack_status 应存在且为 dict
    assert "gstack_status" in loaded, "B2 端到端: 3 轮后 gstack_status 段消失"
    assert isinstance(loaded["gstack_status"], dict)


# ---------------------------------------------------------------------------
# TC-09  test_parse_simple_yaml_scalar_self_heal_multiple_quotes  (B1 self-heal P1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("polluted, expected", [
    ("''", ""),                                            # 2 层 → 空串
    ("''''", ""),                                          # 4 层 → 空串
    ("''''''", ""),                                        # 6 层（当前 runtime 实测）→ 空串
    ("'''2026-05-08T03:30:00.000000+00:00'''", "2026-05-08T03:30:00.000000+00:00"),
    ("'2026-05-08T03:30:00.000000+00:00'", "2026-05-08T03:30:00.000000+00:00"),
    ("'hello'", "hello"),                                  # pyyaml 单层包裹 → 正确剥除
    ("normal_value", "normal_value"),                      # 无引号 → 原样返回
])
def test_parse_simple_yaml_scalar_self_heal_multiple_quotes(polluted: str, expected: str) -> None:
    """_parse_simple_yaml_scalar 应自动剥除多重单引号污染层（用户拍板第 4 条）。"""
    result = wh._parse_simple_yaml_scalar(polluted)
    assert result == expected, (
        f"self-heal 失败: 输入 {polluted!r} → 期望 {expected!r}，实际 {result!r}"
    )


# ---------------------------------------------------------------------------
# TC-10  test_install_agent_active_requirements_preserved  (B3 端到端 P1)
# ---------------------------------------------------------------------------

def test_install_agent_active_requirements_preserved(tmp_path: Path) -> None:
    """_write_gstack_status 后再读 runtime，active_requirements 应保留。

    B3 端到端: _write_gstack_status 原来用 yaml.dump 写，pyyaml block-seq 0 缩进
    导致下次 load_simple_yaml 把 active_requirements 读成 []。
    修复后走 save_requirement_runtime，list 用 2 空格缩进输出，load 可正确识别。
    """
    project = _make_project(tmp_path, active_requirements=["req-54", "req-55"])

    # 执行一次 _write_gstack_status（即 install_agent 末尾调用）
    status = {
        "installed_skills": ["office-hours"],
        "vendor_version": "abc1234",
        "last_install": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "agent_kind_compatible": True,
    }
    wh._write_gstack_status(project, status)

    # 再次 load，检查 active_requirements 保留
    loaded = wh.load_requirement_runtime(project)
    ar = loaded.get("active_requirements", [])
    assert isinstance(ar, list), f"active_requirements 应为 list，实际: {type(ar)}"
    assert "req-54" in ar, (
        f"B3 端到端: _write_gstack_status 后 req-54 从 active_requirements 消失。"
        f"实际: {ar!r}"
    )
    assert "req-55" in ar, (
        f"B3 端到端: _write_gstack_status 后 req-55 从 active_requirements 消失。"
        f"实际: {ar!r}"
    )
