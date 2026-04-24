"""pytest 覆盖：check_contract_triggers 和 run_contract_cli triggers 分支。

req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）/
chg-02（触发门禁 §3.5.2 + harness validate triggers lint）
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from harness_workflow.validate_contract import check_contract_triggers, run_contract_cli


# ────────────────────────────────────────────────
# fixtures
# ────────────────────────────────────────────────

KEYWORDS_YAML_CONTENT = textwrap.dedent("""\
    tools:
      - tool_id: "api-document-upload"
        keywords: ["帮我上传接口文档", "同步接口到 apifox"]
        catalog: "catalog/api-document-upload.md"
        description: "扫描项目 API 定义生成 OpenAPI 并上传到选定 provider"
""")


def _make_harness_manager_md(extra_bullet: str | None = None) -> str:
    """生成含有 §3.5.2 镜像列表的 harness-manager.md 正文。"""
    bullets = "- 帮我上传接口文档\n- 同步接口到 apifox"
    if extra_bullet:
        bullets += f"\n- {extra_bullet}"
    # 不使用 textwrap.dedent + f-string 组合，避免 bullets 多行插入缩进不一致问题
    lines = [
        "# harness-manager",
        "",
        "#### 3.5.2 触发 api-document-upload 召唤（req-38（api-document-upload 工具闭环）/ chg-02（触发门禁 §3.5.2））",
        "",
        "<!-- 镜像自 .workflow/tools/index/keywords.yaml，由 harness validate --contract triggers 保证一致 -->",
    ]
    lines.extend(bullets.splitlines())
    lines += [
        "",
        "（以上列表为单一权威镜像，由 lint 保证同步，不得手工增减。）",
        "",
        "#### 3.6 派发 Subagent",
    ]
    return "\n".join(lines) + "\n"


def _setup_files(tmp_path: Path, extra_bullet: str | None = None) -> None:
    """在 tmp_path 构造最小必要文件结构。"""
    keywords_dir = tmp_path / ".workflow" / "tools" / "index"
    keywords_dir.mkdir(parents=True)
    (keywords_dir / "keywords.yaml").write_text(KEYWORDS_YAML_CONTENT, encoding="utf-8")

    roles_dir = tmp_path / ".workflow" / "context" / "roles"
    roles_dir.mkdir(parents=True)
    (roles_dir / "harness-manager.md").write_text(
        _make_harness_manager_md(extra_bullet), encoding="utf-8"
    )


# ────────────────────────────────────────────────
# test cases
# ────────────────────────────────────────────────


def test_validate_contract_triggers_pass(tmp_path: Path) -> None:
    """两侧关键词一致时，check_contract_triggers 返回 0。"""
    _setup_files(tmp_path)
    rc = check_contract_triggers(tmp_path)
    assert rc == 0, "一致时应退出码 0"


def test_validate_contract_triggers_detect_drift(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """md 故意多加一行触发词时，应返回非 0 且 stderr 含 diff 内容。"""
    _setup_files(tmp_path, extra_bullet="额外触发词")
    rc = check_contract_triggers(tmp_path)
    assert rc != 0, "有 drift 时应退出码非 0"
    captured = capsys.readouterr()
    assert "drift" in captured.err or "额外触发词" in captured.err, (
        f"stderr 应含 drift 信息，实际：{captured.err!r}"
    )


def test_validate_contract_triggers_fallback_missing_keywords_yaml(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """keywords.yaml 缺失时，退出码 0 + stderr warn。"""
    # 只建 harness-manager.md，不建 keywords.yaml
    roles_dir = tmp_path / ".workflow" / "context" / "roles"
    roles_dir.mkdir(parents=True)
    (roles_dir / "harness-manager.md").write_text(
        _make_harness_manager_md(), encoding="utf-8"
    )
    rc = check_contract_triggers(tmp_path)
    assert rc == 0, "keywords.yaml 缺失时应 fallback 退出码 0"
    captured = capsys.readouterr()
    assert "skipped" in captured.err.lower(), f"应有 skipped warn，实际：{captured.err!r}"


def test_validate_contract_triggers_fallback_missing_harness_manager(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """harness-manager.md 缺失时，退出码 0 + stderr warn。"""
    keywords_dir = tmp_path / ".workflow" / "tools" / "index"
    keywords_dir.mkdir(parents=True)
    (keywords_dir / "keywords.yaml").write_text(KEYWORDS_YAML_CONTENT, encoding="utf-8")
    # 不建 harness-manager.md
    rc = check_contract_triggers(tmp_path)
    assert rc == 0, "harness-manager.md 缺失时应 fallback 退出码 0"
    captured = capsys.readouterr()
    assert "skipped" in captured.err.lower(), f"应有 skipped warn，实际：{captured.err!r}"


def test_run_contract_cli_triggers_pass(tmp_path: Path) -> None:
    """run_contract_cli(root, 'triggers') 一致时退出码 0。"""
    _setup_files(tmp_path)
    rc = run_contract_cli(tmp_path, "triggers")
    assert rc == 0


def test_run_contract_cli_triggers_detect_drift(tmp_path: Path) -> None:
    """run_contract_cli(root, 'triggers') 有 drift 时退出码非 0。"""
    _setup_files(tmp_path, extra_bullet="额外触发词")
    rc = run_contract_cli(tmp_path, "triggers")
    assert rc != 0


def test_run_contract_cli_all_includes_triggers(tmp_path: Path) -> None:
    """run_contract_cli(root, 'all') 串联 triggers：一致时退出码 0（regression + 7 均 fallback 空）。"""
    _setup_files(tmp_path)
    rc = run_contract_cli(tmp_path, "all")
    assert rc == 0
