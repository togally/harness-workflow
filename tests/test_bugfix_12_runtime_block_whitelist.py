"""bugfix-12（runtime-block.yaml-误判用户野文件-白名单漏配）反例测试。

覆盖范围：
- TC-01：非 dev_repo + runtime-block.yaml 存在 → check_user_write_protected_zones return 0（不误报）
- TC-02：非 dev_repo + 真野文件 + runtime-block.yaml 同时存在 → return 1，violations 含野文件但不含 runtime-block.yaml
- TC-03：白名单条目锁定 lint —— assert "state/runtime-block.yaml" in _SCAFFOLD_V2_MIRROR_WHITELIST
- TC-04：dev_repo + runtime-block.yaml + 野文件 → return 0（dev mode 自动豁免）
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.validate_contract import check_user_write_protected_zones  # noqa: E402
from harness_workflow.workflow_helpers import _SCAFFOLD_V2_MIRROR_WHITELIST  # noqa: E402


# ─────────────────────────────────────────────
# TC-01：非 dev_repo + runtime-block.yaml 存在 → rc == 0（白名单命中，不误报）
# ─────────────────────────────────────────────

def test_tc01_runtime_block_yaml_not_flagged_in_user_repo(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """TC-01：非 dev_repo（无 pyproject + 无 src/harness_workflow + 无 env）
    + .workflow/state/runtime-block.yaml 存在 → rc == 0（白名单命中，不误报）。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 构造非 dev_repo：无 pyproject.toml，无 src/harness_workflow
    block_file = tmp_path / ".workflow" / "state" / "runtime-block.yaml"
    block_file.parent.mkdir(parents=True, exist_ok=True)
    block_file.write_text("error_type: schema-audit\nseverity: FAIL\n", encoding="utf-8")

    rc = check_user_write_protected_zones(tmp_path)
    captured = capsys.readouterr()

    assert rc == 0, (
        f"runtime-block.yaml should be whitelisted and not flagged; got rc={rc}\n"
        f"stderr:\n{captured.err!r}"
    )
    assert "runtime-block.yaml" not in captured.err, (
        f"runtime-block.yaml should not appear in violations; got stderr:\n{captured.err!r}"
    )


# ─────────────────────────────────────────────
# TC-02：非 dev_repo + runtime-block.yaml + 真野文件 → rc == 1，仅野文件报，runtime-block 不报
# ─────────────────────────────────────────────

def test_tc02_runtime_block_yaml_whitelisted_while_wild_file_flagged(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """TC-02：非 dev_repo + runtime-block.yaml + 真野文件（.workflow/context/roles/my-custom.md）
    → rc == 1，violations 含 my-custom.md 但不含 runtime-block.yaml（豁免精准）。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # runtime-block.yaml（应被豁免）
    block_file = tmp_path / ".workflow" / "state" / "runtime-block.yaml"
    block_file.parent.mkdir(parents=True, exist_ok=True)
    block_file.write_text("error_type: schema-audit\nseverity: FAIL\n", encoding="utf-8")

    # 真野文件（应被报）
    wild_file = tmp_path / ".workflow" / "context" / "roles" / "my-custom.md"
    wild_file.parent.mkdir(parents=True, exist_ok=True)
    wild_file.write_text("# My Custom Role\n", encoding="utf-8")

    rc = check_user_write_protected_zones(tmp_path)
    captured = capsys.readouterr()

    assert rc == 1, (
        f"Wild file should trigger violation (rc=1); got rc={rc}\n"
        f"stderr:\n{captured.err!r}"
    )
    assert "my-custom.md" in captured.err, (
        f"Expected 'my-custom.md' in violations; got:\n{captured.err!r}"
    )
    assert "runtime-block.yaml" not in captured.err, (
        f"runtime-block.yaml should be whitelisted and not appear in violations; got:\n{captured.err!r}"
    )


# ─────────────────────────────────────────────
# TC-03：白名单条目锁定 lint（防止后续 chg 误删）
# ─────────────────────────────────────────────

def test_tc03_runtime_block_yaml_in_whitelist() -> None:
    """TC-03：直接断言 'state/runtime-block.yaml' 在 _SCAFFOLD_V2_MIRROR_WHITELIST 中
    （防御性锁定，防止后续 chg 误删白名单条目）。
    """
    assert "state/runtime-block.yaml" in _SCAFFOLD_V2_MIRROR_WHITELIST, (
        "'state/runtime-block.yaml' must be present in _SCAFFOLD_V2_MIRROR_WHITELIST "
        "(bugfix-12 fix). Entry appears to have been removed."
    )


# ─────────────────────────────────────────────
# TC-04：dev_repo 行为不变（dev mode 自动豁免，与本 fix 无关）
# ─────────────────────────────────────────────

def test_tc04_dev_repo_still_short_circuits(tmp_path: Path, monkeypatch, capsys) -> None:
    """TC-04：dev_repo（pyproject name=harness-workflow）+ runtime-block.yaml + 野文件
    → rc == 0（dev 短路，本 fix 不改变 dev_repo 行为）。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 构造 dev_repo：pyproject.toml name = "harness-workflow"
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "harness-workflow"\nversion = "0.1.0"\n', encoding="utf-8")

    # runtime-block.yaml
    block_file = tmp_path / ".workflow" / "state" / "runtime-block.yaml"
    block_file.parent.mkdir(parents=True, exist_ok=True)
    block_file.write_text("error_type: schema-audit\nseverity: FAIL\n", encoding="utf-8")

    # 野文件（dev_repo 短路，不会扫描）
    wild_file = tmp_path / ".workflow" / "context" / "roles" / "my-custom.md"
    wild_file.parent.mkdir(parents=True, exist_ok=True)
    wild_file.write_text("# Custom\n", encoding="utf-8")

    rc = check_user_write_protected_zones(tmp_path)
    captured = capsys.readouterr()

    assert rc == 0, (
        f"dev_repo should always return 0 (short-circuit); got rc={rc}\n"
        f"stderr:\n{captured.err!r}"
    )
    assert "violation" not in captured.err, (
        f"dev_repo should produce no violation output; got:\n{captured.err!r}"
    )
