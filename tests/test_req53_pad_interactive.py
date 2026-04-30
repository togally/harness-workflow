"""req-53 / chg-04: _pad_interactive questionary 引导。

覆盖：
- TC-01: 非 TTY abort
- TC-02: questionary mock → 文件落位
- TC-03: questionary cancel → exit=1
- TC-04: tool kind 不需要 scope step
"""
from __future__ import annotations

import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _env() -> dict:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}:{existing}" if existing else src_path
    return env


def _run_install(cwd: Path) -> None:
    r = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
        env=_env(),
    )
    assert r.returncode == 0, f"install failed: {r.stderr}"


def test_tc01_interactive_非TTY_abort(tmp_path: Path) -> None:
    """TC-01: 非 TTY 下裸跑 pad → stderr 含 interactive 提示 + exit≠0."""
    r = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "pad"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        encoding="utf-8",
        env=_env(),
        stdin=subprocess.DEVNULL,
    )
    assert r.returncode != 0, f"期望非零退出码，实际 stdout={r.stdout}\nstderr={r.stderr}"
    assert "interactive" in r.stderr or "TTY" in r.stderr, \
        f"stderr 缺 interactive/TTY 提示: {r.stderr}"


def test_tc02_interactive_questionary_mock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-02: monkeypatch questionary → 文件落位与位置参数版本一致."""
    _run_install(tmp_path)
    # monkeypatch sys.stdin.isatty → True
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(isatty=lambda: True))

    import questionary as _q

    call_count = {"n": 0}

    def mock_select(message: str, choices=None, default=None, **kwargs):
        class Ans:
            def ask(self):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    return "rule"  # kind
                return "coding"   # scope

        return Ans()

    def mock_text(message: str, validate=None, **kwargs):
        class Ans:
            def ask(self):
                return "mock-测试规则"

        return Ans()

    monkeypatch.setattr(_q, "select", mock_select)
    monkeypatch.setattr(_q, "text", mock_text)

    from harness_workflow.workflow_helpers import _pad_interactive

    rc = _pad_interactive(tmp_path)
    assert rc == 0, f"_pad_interactive 返回 {rc}"
    # 验证文件落位
    constraint_dir = tmp_path / "artifacts" / "project" / "constraints" / "coding"
    files = list(constraint_dir.glob("*.md")) if constraint_dir.exists() else []
    assert files, f"文件未落位到 constraints/coding/: {list(constraint_dir.iterdir()) if constraint_dir.exists() else '目录不存在'}"


def test_tc03_interactive_cancel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-03: questionary cancel（返回 None）→ exit=1 + stdout 含 cancelled."""
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(isatty=lambda: True))

    import questionary as _q

    def mock_select_cancel(message: str, choices=None, default=None, **kwargs):
        class Ans:
            def ask(self):
                return None  # user Ctrl-C

        return Ans()

    monkeypatch.setattr(_q, "select", mock_select_cancel)

    from harness_workflow.workflow_helpers import _pad_interactive
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        rc = _pad_interactive(tmp_path)
    out = f.getvalue()
    assert rc == 1, f"cancel 应返回 1，实际 {rc}"
    assert "cancelled" in out, f"stdout 缺 cancelled: {out}"


def test_tc04_interactive_tool_no_scope_step(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-04: kind=tool 时不触发 scope select（PAD_KINDS["tool"] = []）."""
    _run_install(tmp_path)
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(isatty=lambda: True))

    import questionary as _q

    select_calls: list[str] = []

    def mock_select(message: str, choices=None, default=None, **kwargs):
        class Ans:
            def ask(self):
                select_calls.append(message)
                return "tool"  # 只被调用一次（kind 选择）

        return Ans()

    def mock_text(message: str, validate=None, **kwargs):
        class Ans:
            def ask(self):
                return "test-tool"

        return Ans()

    monkeypatch.setattr(_q, "select", mock_select)
    monkeypatch.setattr(_q, "text", mock_text)

    from harness_workflow.workflow_helpers import _pad_interactive

    rc = _pad_interactive(tmp_path)
    assert rc == 0, f"_pad_interactive 返回 {rc}"
    # tool kind → select 应只被调用 1 次（kind 选择，无 scope 选择）
    assert len(select_calls) == 1, f"tool kind 不应触发 scope select，实际 select 调用 {len(select_calls)} 次: {select_calls}"
