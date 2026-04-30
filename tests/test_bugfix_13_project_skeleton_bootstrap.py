"""bugfix-13（install时自动创建artifacts-project骨架与索引模板）测试。

覆盖范围（诊断 §测试用例设计 12 TC 中的 ≥ 6 TC）：
- TC-01：fresh repo `harness install` → artifacts/project/ 全部 10 文件创建
- TC-02：二次 `harness install` → 幂等，skipped=10（0 新建）
- TC-03：用户已有 my-rule.md → install → my-rule.md 保留 + 骨架文件新建
- TC-04：用户改了 README.md → install → 用户改动保留（write_if_missing 不覆盖）
- TC-05：`harness install --check` → dry-run 输出 "would create" + 实际不写盘
- TC-06：bootstrap 写盘后 `_load_project_level_index` 能正常解析（链路联动）
- TC-07：模板文件清单核查（10 文件齐全）
- TC-08：`_bootstrap_project_skeleton` helper 直调（单元测试）
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import (  # noqa: E402
    _bootstrap_project_skeleton,
    _load_project_level_index,
)

# 模板骨架根（用于 TC-07 文件清单断言）
_SKELETON_ROOT = (
    REPO_ROOT / "src" / "harness_workflow" / "assets" / "templates" / "project-skeleton"
)

# 期望的 10 个相对路径（相对 project-skeleton/）
_EXPECTED_FILES = {
    "README.md",
    "constraints/.gitkeep",
    "constraints/index.md",
    "experience/.gitkeep",
    "experience/roles/index.md",
    "experience/tool/index.md",
    "experience/risk/index.md",
    "experience/regression/index.md",
    "experience/stage/index.md",
    "tools/.gitkeep",
}


def _subprocess_env() -> dict:
    """Return env with PYTHONPATH pointing to workspace src/."""
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}:{existing}" if existing else src_path
    return env


def _run_harness(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run harness_workflow.cli in subprocess and return result."""
    return subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=90,
        env=_subprocess_env(),
    )


# ─────────────────────────────────────────────
# TC-07：模板文件清单核查（10 文件齐全）
# ─────────────────────────────────────────────

def test_tc07_skeleton_template_files_complete() -> None:
    """TC-07：assets/templates/project-skeleton/ 包含恰好 10 个文件，文件名与预期列表一致。"""
    assert _SKELETON_ROOT.exists(), f"模板根目录不存在：{_SKELETON_ROOT}"
    actual = {
        f.relative_to(_SKELETON_ROOT).as_posix()
        for f in _SKELETON_ROOT.rglob("*")
        if f.is_file()
    }
    assert actual == _EXPECTED_FILES, (
        f"模板文件列表不匹配。\n期望：{sorted(_EXPECTED_FILES)}\n实际：{sorted(actual)}"
    )
    assert len(actual) == 10, f"期望 10 个文件，实际 {len(actual)} 个：{sorted(actual)}"


# ─────────────────────────────────────────────
# TC-08：_bootstrap_project_skeleton helper 直调（单元测试）
# ─────────────────────────────────────────────

def test_tc08_bootstrap_helper_fresh(tmp_path: Path) -> None:
    """TC-08a：fresh tmpdir 直调 _bootstrap_project_skeleton → 返回 10 条 created actions。"""
    actions = _bootstrap_project_skeleton(tmp_path, check=False)
    # 应当 created 10 个文件
    created_actions = [a for a in actions if a.startswith("created ")]
    assert len(created_actions) == 10, (
        f"期望 10 条 created actions，实际 {len(created_actions)}: {actions}"
    )
    # 所有 10 个目标文件应存在
    for rel in _EXPECTED_FILES:
        target = tmp_path / "artifacts" / "project" / rel
        assert target.exists(), f"期望文件不存在：{target}"


def test_tc08b_bootstrap_helper_idempotent(tmp_path: Path) -> None:
    """TC-08b：第二次调 _bootstrap_project_skeleton → 返回空列表（全部 skipped）。"""
    _bootstrap_project_skeleton(tmp_path, check=False)
    actions = _bootstrap_project_skeleton(tmp_path, check=False)
    assert actions == [], f"期望幂等，第二次应返回空列表，实际: {actions}"


def test_tc08c_bootstrap_helper_check_mode(tmp_path: Path) -> None:
    """TC-08c：check=True → 返回 would-create actions + 不写盘。"""
    actions = _bootstrap_project_skeleton(tmp_path, check=True)
    assert len(actions) == 10, f"check mode 应返回 10 条 would-create，实际 {len(actions)}: {actions}"
    for a in actions:
        assert a.startswith("would create "), f"check mode 动作应以 'would create ' 开头：{a!r}"
    # 不写盘：artifacts/project/ 不存在
    assert not (tmp_path / "artifacts" / "project").exists(), (
        "check=True 不应写盘，但 artifacts/project/ 已存在"
    )


# ─────────────────────────────────────────────
# TC-01：fresh repo `harness install` → 全部 10 文件创建
# ─────────────────────────────────────────────

def test_tc01_fresh_repo_install_creates_skeleton(tmp_path: Path) -> None:
    """TC-01：fresh repo `harness install` → artifacts/project/ 下 10 个骨架文件全部创建。
    AC-01（fresh repo bootstrap）。P0。
    """
    result = _run_harness(tmp_path, "install")
    assert result.returncode == 0, (
        f"harness install 失败。\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    # 断言 10 个文件存在
    for rel in _EXPECTED_FILES:
        target = tmp_path / "artifacts" / "project" / rel
        assert target.exists(), (
            f"骨架文件不存在：{target}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    # 断言 10 个文件（find -type f）
    actual_files = list((tmp_path / "artifacts" / "project").rglob("*"))
    actual_files = [f for f in actual_files if f.is_file()]
    assert len(actual_files) == 10, (
        f"期望 10 个文件，实际 {len(actual_files)}: {[str(f.relative_to(tmp_path)) for f in actual_files]}"
    )
    # stderr 含 project skeleton 日志
    assert "project skeleton: created 10 files" in result.stderr, (
        f"stderr 应含 'project skeleton: created 10 files'，实际 stderr:\n{result.stderr}"
    )


# ─────────────────────────────────────────────
# TC-02：二次 install → 幂等（skipped=10）
# ─────────────────────────────────────────────

def test_tc02_idempotent_second_install(tmp_path: Path) -> None:
    """TC-02：二次 `harness install` → 幂等，skipped=10 / created=0。
    AC-02（幂等）。P0。
    """
    # 第一次
    result1 = _run_harness(tmp_path, "install")
    assert result1.returncode == 0, f"第一次 install 失败: {result1.stderr}"

    # 记录 README.md 内容以验证不被覆盖
    readme_content = (tmp_path / "artifacts" / "project" / "README.md").read_text(encoding="utf-8")

    # 第二次
    result2 = _run_harness(tmp_path, "install")
    assert result2.returncode == 0, f"第二次 install 失败: {result2.stderr}"
    # stderr 含 created 0 + skipped 10
    assert "project skeleton: created 0 files / skipped 10 files" in result2.stderr, (
        f"二次 install 应含 'created 0 files / skipped 10 files'，实际 stderr:\n{result2.stderr}"
    )
    # 核心文件内容不变
    assert (tmp_path / "artifacts" / "project" / "README.md").read_text(encoding="utf-8") == readme_content


# ─────────────────────────────────────────────
# TC-03：用户已有 my-rule.md → 保留 + 骨架文件新建
# ─────────────────────────────────────────────

def test_tc03_preserve_user_rule(tmp_path: Path) -> None:
    """TC-03：用户已有 artifacts/project/constraints/my-rule.md → install → my-rule.md 保留 + 骨架文件新建。
    AC-03（用户写入保留）。P0。
    """
    # 先写用户自定义文件
    user_rule = tmp_path / "artifacts" / "project" / "constraints" / "my-rule.md"
    user_rule.parent.mkdir(parents=True, exist_ok=True)
    user_rule.write_text("USER_CONTENT: 我的项目约束\n", encoding="utf-8")

    result = _run_harness(tmp_path, "install")
    assert result.returncode == 0, f"install 失败: {result.stderr}"

    # 用户文件字节级保留
    assert user_rule.read_text(encoding="utf-8") == "USER_CONTENT: 我的项目约束\n", (
        "用户自定义 my-rule.md 被覆盖或修改"
    )
    # 骨架文件 constraints/index.md 也被创建
    assert (tmp_path / "artifacts" / "project" / "constraints" / "index.md").exists()
    # 骨架 README.md 被创建
    assert (tmp_path / "artifacts" / "project" / "README.md").exists()


# ─────────────────────────────────────────────
# TC-04：用户改了 README.md → 保留（write_if_missing 不覆盖）
# ─────────────────────────────────────────────

def test_tc04_preserve_user_edited_readme(tmp_path: Path) -> None:
    """TC-04：用户改了 artifacts/project/README.md → install → 用户改动保留（write_if_missing 不覆盖）。
    AC-04（不覆盖用户改动）。P0。
    """
    # 先写用户自定义 README
    user_readme = tmp_path / "artifacts" / "project" / "README.md"
    user_readme.parent.mkdir(parents=True, exist_ok=True)
    user_readme.write_text("MY_CUSTOM_README: 用户自定义顶级 README\n", encoding="utf-8")

    result = _run_harness(tmp_path, "install")
    assert result.returncode == 0, f"install 失败: {result.stderr}"

    # README 内容为用户写的，未被模板覆盖
    assert user_readme.read_text(encoding="utf-8") == "MY_CUSTOM_README: 用户自定义顶级 README\n", (
        "用户自定义 README.md 被模板覆盖"
    )
    # 其他骨架文件（未预先存在的）应被创建
    assert (tmp_path / "artifacts" / "project" / "constraints" / "index.md").exists()


# ─────────────────────────────────────────────
# TC-05：`harness install --check` → dry-run 不写盘
# ─────────────────────────────────────────────

def test_tc05_check_mode_no_write(tmp_path: Path) -> None:
    """TC-05：`harness install --check` → dry-run 输出 "would create" + 实际不写盘。
    AC-05（check mode）。P1。
    """
    result = _run_harness(tmp_path, "install", "--check")
    assert result.returncode == 0, (
        f"harness install --check 失败。\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    # stdout 应含 "would create artifacts/project/" 相关行
    combined = result.stdout + result.stderr
    assert "would create artifacts/project/" in combined, (
        f"check mode 应输出 'would create artifacts/project/' 行，实际 stdout+stderr:\n{combined}"
    )
    # artifacts/project/ 不存在（不写盘）
    assert not (tmp_path / "artifacts" / "project").exists(), (
        "check mode 不应写盘，但 artifacts/project/ 已存在"
    )


# ─────────────────────────────────────────────
# TC-06：bootstrap 写盘后 _load_project_level_index 能正常解析
# ─────────────────────────────────────────────

def test_tc06_load_index_works_after_bootstrap(tmp_path: Path) -> None:
    """TC-06：bootstrap 写盘后 _load_project_level_index 能正常解析各 scope。
    AC-08（与 req-52 / chg-03 链路联动）。P1。
    """
    # 直调 helper bootstrap
    _bootstrap_project_skeleton(tmp_path, check=False)

    # 对每个 scope 调 _load_project_level_index，解析 index.md
    # 骨架 index.md 内只有注释行（<!--...-->），解析应返回 [] 或非 None
    for scope in (
        "constraints",
        "experience-roles",
        "experience-tool",
        "experience-risk",
        "experience-regression",
        "experience-stage",
    ):
        result = _load_project_level_index(tmp_path, scope)
        # 返回类型必须是 list（可以是空列表，注释行不计入条目）
        assert isinstance(result, list), (
            f"scope={scope}: _load_project_level_index 应返回 list，实际类型 {type(result)}"
        )

    # 写入一条真实条目后验证能解析
    roles_idx = tmp_path / "artifacts" / "project" / "experience" / "roles" / "index.md"
    # 追加一行真实数据
    original = roles_idx.read_text(encoding="utf-8")
    new_row = "| my-exp.md | 项目独有 analyst 经验覆盖 | experience-roles | always |  |\n"
    # 在表头行之后、> 说明之前插入数据行（追加到表格末尾）
    # 简单做法：直接在尾部写入不会破坏 schema，直接替换空表格行
    patched = original.replace(
        "| <!-- 示例：analyst-override.md --> | <!-- 示例：项目独有的 analyst 经验覆盖 --> | experience-roles | always | <!-- 加载时机：always / on-stage:executing / on-keyword:lint --> |",
        "| my-exp.md | 项目独有 analyst 经验覆盖 | experience-roles | always |  |",
    )
    roles_idx.write_text(patched, encoding="utf-8")

    entries = _load_project_level_index(tmp_path, "experience-roles")
    assert isinstance(entries, list)
    assert len(entries) >= 1, (
        f"写入真实条目后，_load_project_level_index 应返回 ≥ 1 条目，实际 {entries}"
    )
    first = entries[0]
    assert first.get("path") == "my-exp.md", f"path 字段应为 'my-exp.md'，实际 {first}"
    assert first.get("scope") == "experience-roles", f"scope 字段不匹配：{first}"
    assert first.get("source") == "main", f"source 应为 'main'，实际 {first}"
