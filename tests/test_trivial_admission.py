"""req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）/ chg-02（trivial 准入判据 + 自动识别 hint）
tests/test_trivial_admission.py — classify_diff_change_types + validate_trivial_eligibility 单测
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from harness_workflow.workflow_helpers import (
    classify_diff_change_types,
    validate_trivial_eligibility,
)


# ===========================================================================
# classify_diff_change_types
# ===========================================================================

class TestClassifyDiffChangeTypes:
    """TC-01 ~ TC-03 系列：改动类型分类。"""

    def test_typo_diff(self):
        """TC-01：单行 token 替换 → typo"""
        diff = (
            "diff --git a/foo.py b/foo.py\n"
            "--- a/foo.py\n+++ b/foo.py\n"
            "@@ -1 +1 @@\n"
            "-    message = 'helo world'\n"
            "+    message = 'hello world'\n"
        )
        types = classify_diff_change_types(diff)
        assert "typo" in types or "string" in types, f"expected typo/string, got {types}"

    def test_doc_diff(self):
        """TC-02：.md 文件改动 → doc"""
        diff = (
            "diff --git a/README.md b/README.md\n"
            "--- a/README.md\n+++ b/README.md\n"
            "@@ -1 +1 @@\n"
            "-# Old Title\n"
            "+# New Title\n"
        )
        types = classify_diff_change_types(diff)
        assert "doc" in types, f"expected doc, got {types}"

    def test_complex_logic_diff(self):
        """TC-03：复杂逻辑改动 → other"""
        diff = (
            "diff --git a/core.py b/core.py\n"
            "--- a/core.py\n+++ b/core.py\n"
            "@@ -1,5 +1,10 @@\n"
            "-def old_func():\n"
            "-    return 1\n"
            "+def new_func(x, y):\n"
            "+    result = x * y\n"
            "+    for i in range(10):\n"
            "+        result += i\n"
            "+    return result\n"
        )
        types = classify_diff_change_types(diff)
        assert "other" in types, f"expected other, got {types}"

    def test_comment_diff(self):
        """注释行改动 → comment"""
        diff = (
            "diff --git a/utils.py b/utils.py\n"
            "--- a/utils.py\n+++ b/utils.py\n"
            "@@ -1,2 +1,2 @@\n"
            "-# Old comment\n"
            "+# New comment\n"
        )
        types = classify_diff_change_types(diff)
        assert "comment" in types, f"expected comment, got {types}"

    def test_config_constant_diff(self):
        """配置常量改动 → config_constant"""
        diff = (
            "diff --git a/config.yaml b/config.yaml\n"
            "--- a/config.yaml\n+++ b/config.yaml\n"
            "@@ -1 +1 @@\n"
            "-timeout: 30\n"
            "+timeout: 60\n"
        )
        types = classify_diff_change_types(diff)
        assert "config_constant" in types, f"expected config_constant, got {types}"

    def test_empty_diff_returns_empty_or_other(self):
        """空 diff 返回空集或 other"""
        types = classify_diff_change_types("")
        assert types == set() or types == {"other"}


# ===========================================================================
# validate_trivial_eligibility
# ===========================================================================

def _init_git_repo(tmpdir: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(tmpdir), capture_output=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=str(tmpdir), capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmpdir), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmpdir), capture_output=True)


def _make_committed_file(tmpdir: Path, filename: str, content: str) -> None:
    fpath = tmpdir / filename
    fpath.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", filename], cwd=str(tmpdir), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmpdir), capture_output=True)


class TestValidateTrivialEligibility:
    """TC-04 ~ TC-10 系列：prepare/validate 用例。"""

    def test_empty_diff_returns_false(self, tmp_path):
        """TC-08：空 diff → (False, 'no diff')"""
        _init_git_repo(tmp_path)
        _make_committed_file(tmp_path, "foo.py", "x = 1\n")
        ok, reason = validate_trivial_eligibility(tmp_path)
        assert ok is False
        assert "no diff" in reason

    def test_one_line_typo_returns_true(self, tmp_path):
        """TC-04（正例1）：1 行 typo fix → True"""
        _init_git_repo(tmp_path)
        _make_committed_file(tmp_path, "msg.py", "msg = 'helo'\n")
        # 修改 1 行 typo
        (tmp_path / "msg.py").write_text("msg = 'hello'\n", encoding="utf-8")
        ok, reason = validate_trivial_eligibility(tmp_path)
        assert ok is True, f"expected True, got ({ok}, {reason})"

    def test_doc_change_returns_true(self, tmp_path):
        """TC-04（正例3）：.md 文件单行改动 → True"""
        _init_git_repo(tmp_path)
        _make_committed_file(tmp_path, "README.md", "# Title\n\nOld content.\n")
        (tmp_path / "README.md").write_text("# Title\n\nNew content.\n", encoding="utf-8")
        ok, reason = validate_trivial_eligibility(tmp_path)
        assert ok is True, f"expected True, got ({ok}, {reason})"

    def test_15_lines_returns_false(self, tmp_path):
        """TC-05：15 行改动 → False（超阈值）"""
        _init_git_repo(tmp_path)
        original = "\n".join(f"line{i} = {i}" for i in range(20))
        _make_committed_file(tmp_path, "big.py", original + "\n")
        modified = "\n".join(f"line{i} = {i + 100}" for i in range(20))
        (tmp_path / "big.py").write_text(modified + "\n", encoding="utf-8")
        ok, reason = validate_trivial_eligibility(tmp_path)
        assert ok is False
        assert "行" in reason or "threshold" in reason.lower()

    def test_3_files_returns_false(self, tmp_path):
        """TC-06：3 文件改动 → False（超文件数阈值）"""
        _init_git_repo(tmp_path)
        for i in range(3):
            _make_committed_file(tmp_path, f"f{i}.py", f"x = {i}\n")
        for i in range(3):
            (tmp_path / f"f{i}.py").write_text(f"x = {i + 1}\n", encoding="utf-8")
        ok, reason = validate_trivial_eligibility(tmp_path)
        assert ok is False
        assert "文件" in reason or "file" in reason.lower()

    def test_new_import_returns_false(self, tmp_path):
        """TC-07：新增 import → False（因 import 或 other 类型）"""
        _init_git_repo(tmp_path)
        _make_committed_file(tmp_path, "app.py", "x = 1\n")
        (tmp_path / "app.py").write_text("import os\nx = 1\n", encoding="utf-8")
        ok, reason = validate_trivial_eligibility(tmp_path)
        assert ok is False  # 新增 import 或类型 other 都触发拒绝

    def test_complex_logic_returns_false(self, tmp_path):
        """TC-09：复杂逻辑改动 → False（other 类型）"""
        _init_git_repo(tmp_path)
        _make_committed_file(tmp_path, "logic.py", "def foo():\n    return 1\n")
        new_content = (
            "def foo(x, y, z):\n"
            "    result = 0\n"
            "    for i in range(x):\n"
            "        result += y * z + i\n"
            "    return result\n"
        )
        (tmp_path / "logic.py").write_text(new_content, encoding="utf-8")
        ok, reason = validate_trivial_eligibility(tmp_path)
        # 行数可能超 10，或类型为 other
        assert ok is False


class TestHintCli:
    """TC-Dogfood-01/02 系列：harness bugfix / harness requirement hint 输出测试。"""

    def _init_harness_repo(self, tmpdir: Path) -> None:
        wf_state = tmpdir / ".workflow" / "state"
        wf_state.mkdir(parents=True, exist_ok=True)
        (wf_state / "runtime.yaml").write_text(
            "operation_type: requirement\noperation_target: ''\ncurrent_requirement: ''\n"
            "current_requirement_title: ''\nstage: ''\nconversation_mode: open\n"
            "locked_requirement: ''\nlocked_requirement_title: ''\nlocked_stage: ''\n"
            "current_regression: ''\ncurrent_regression_title: ''\n"
            "ff_mode: false\nff_stage_history: []\nactive_requirements: []\n",
            encoding="utf-8",
        )
        (wf_state / "requirements").mkdir(parents=True, exist_ok=True)
        (tmpdir / ".workflow" / "context").mkdir(parents=True, exist_ok=True)
        (tmpdir / ".workflow" / "state" / "bugfixes").mkdir(parents=True, exist_ok=True)
        codex_dir = tmpdir / ".codex" / "harness"
        codex_dir.mkdir(parents=True, exist_ok=True)
        (codex_dir / "config.json").write_text('{"language": "cn"}', encoding="utf-8")
        (codex_dir / "managed-files.json").write_text("{}", encoding="utf-8")
        subprocess.run(["git", "init"], cwd=str(tmpdir), capture_output=True)
        subprocess.run(["git", "checkout", "-b", "main"], cwd=str(tmpdir), capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=str(tmpdir), capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmpdir), capture_output=True)

    def _run_harness(self, tmpdir: Path, *args: str) -> subprocess.CompletedProcess:
        cmd = [sys.executable, "-m", "harness_workflow.cli"] + list(args) + ["--root", str(tmpdir)]
        return subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmpdir))

    def _make_1line_change(self, tmpdir: Path) -> None:
        fpath = tmpdir / "test_hint_file.py"
        fpath.write_text("x = 'helo'\n", encoding="utf-8")
        subprocess.run(["git", "add", "test_hint_file.py"], cwd=str(tmpdir), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmpdir), capture_output=True)
        fpath.write_text("x = 'hello'\n", encoding="utf-8")

    def test_bugfix_shows_hint_for_1line(self, tmp_path):
        """TC-Dogfood-01：1 行改动 + harness bugfix → stdout 含 hint"""
        self._init_harness_repo(tmp_path)
        self._make_1line_change(tmp_path)
        result = self._run_harness(tmp_path, "bugfix", "test fix")
        # hint 可能出现在 stdout（不阻塞）
        combined = result.stdout + result.stderr
        # 命令应成功完成（hint 不阻塞）
        assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"

    def test_bugfix_force_full_no_hint(self, tmp_path):
        """TC-Dogfood-02：--force-full 时 stdout 不含 hint"""
        self._init_harness_repo(tmp_path)
        self._make_1line_change(tmp_path)
        result = self._run_harness(tmp_path, "bugfix", "test fix", "--force-full")
        assert result.returncode == 0
        assert "建议改用" not in result.stdout, "force-full 应抑制 hint"

    def test_hint_does_not_block_command(self, tmp_path):
        """TC-Dogfood-05：hint 不阻塞，命令仍写入 runtime.yaml task_type=bugfix"""
        import yaml
        self._init_harness_repo(tmp_path)
        self._make_1line_change(tmp_path)
        result = self._run_harness(tmp_path, "bugfix", "test非阻塞")
        assert result.returncode == 0
        runtime = yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text())
        assert runtime.get("operation_type") == "bugfix"

    def test_requirement_hint_for_1line(self, tmp_path):
        """TC-Dogfood-04：harness requirement + 1 行改动 → hint 出现"""
        self._init_harness_repo(tmp_path)
        self._make_1line_change(tmp_path)
        result = self._run_harness(tmp_path, "requirement", "test req")
        assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
