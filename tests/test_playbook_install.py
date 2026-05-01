"""tests/test_playbook_install.py

req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-03（harness install 追加路书初始化）
chg-D（精简命令体系）：删除 --skip-playbook / --playbook-only flag 相关 TC，
install 始终装路书骨架 + 不输出 [ASSISTANT INSTRUCTION] 强指令提示。

pytest 测试套件（≥ 8 TC）

TC-01: Level-1 src/modules/* 推断
TC-02: Level-2 src/domains/* 推断
TC-03: Level-3 app/* 推断
TC-04: Level-4 单包次级模块兜底（src/{pkg}/*次级模块，OQ-4=B-modified）
TC-05: dogfood subprocess install（创建骨架 + stdout 断言 + 幂等）
TC-06: install 默认装路书骨架（chg-D：无 flag 也装路书）
TC-07: install 不输出 [ASSISTANT INSTRUCTION]（chg-D：提示句移到 refresh 触发）
TC-08: install --no-llm 不输出 [ASSISTANT INSTRUCTION]（chg-D：提示移到 refresh）
TC-09: render_skeleton 4 顶层文件存在
TC-10: render_skeleton domains 4 件套存在
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
sys.path.insert(0, SRC_DIR)

from harness_workflow.playbook.domain_inference import infer_domains
from harness_workflow.playbook.skeleton import render_skeleton, PLAYBOOK_ROOT_SUFFIX


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_git(root: Path) -> None:
    """最小 git 初始化（install_repo 内部依赖 git 命令）。"""
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True, capture_output=True)


def _run_cli(tmpdir: Path, *extra_args: str) -> subprocess.CompletedProcess:
    """跑 harness_workflow.cli install 子命令（subprocess，透传 extra_args）。

    设置 PYTHONPATH 以指向 worktree 的 src/ 目录，让 subprocess 能 import harness_workflow。
    """
    import os
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_DIR}:{existing_pythonpath}" if existing_pythonpath else SRC_DIR

    cmd = [
        sys.executable, "-m", "harness_workflow.cli",
        "install", "--root", str(tmpdir),
        "--agent", "claude",
        *extra_args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


# ---------------------------------------------------------------------------
# TC-01: Level-1 src/modules/*
# ---------------------------------------------------------------------------

def test_tc01_domain_inference_level1_modules(tmp_path, capsys):
    """TC-01: 推断 Level-1 src/modules/*（auth, order）。"""
    (tmp_path / "src" / "modules" / "auth").mkdir(parents=True)
    (tmp_path / "src" / "modules" / "order").mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "src/modules/*"
    assert set(domains) == {"auth", "order"}
    assert "matched 'src/modules/*'" in captured.out
    assert "auth" in captured.out
    assert "order" in captured.out


# ---------------------------------------------------------------------------
# TC-02: Level-2 src/domains/*
# ---------------------------------------------------------------------------

def test_tc02_domain_inference_level2_domains(tmp_path, capsys):
    """TC-02: 推断 Level-2 src/domains/*（user, payment）。"""
    (tmp_path / "src" / "domains" / "user").mkdir(parents=True)
    (tmp_path / "src" / "domains" / "payment").mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "src/domains/*"
    assert set(domains) == {"user", "payment"}
    assert "matched 'src/domains/*'" in captured.out


# ---------------------------------------------------------------------------
# TC-03: Level-3 app/*
# ---------------------------------------------------------------------------

def test_tc03_domain_inference_level3_app(tmp_path, capsys):
    """TC-03: 推断 Level-3 app/*（web, worker）。"""
    (tmp_path / "app" / "web").mkdir(parents=True)
    (tmp_path / "app" / "worker").mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "app/*"
    assert set(domains) == {"web", "worker"}
    assert "matched 'app/*'" in captured.out


# ---------------------------------------------------------------------------
# TC-04: Level-4 单包次级模块兜底
# ---------------------------------------------------------------------------

def test_tc04_domain_inference_level4_single_pkg(tmp_path, capsys):
    """TC-04: 推断 Level-4 src/{pkg}/*次级模块（OQ-4=B-modified 兜底）。"""
    # 建 pyproject.toml 声明 pkg name
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "mypkg"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    # 建 src/mypkg/{bar, baz}/
    (tmp_path / "src" / "mypkg" / "bar").mkdir(parents=True)
    (tmp_path / "src" / "mypkg" / "baz").mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "src/{pkg}/*次级模块"
    assert set(domains) == {"bar", "baz"}
    assert "matched 'src/mypkg/*次级模块'" in captured.out  # {pkg} 已替换为 mypkg


# ---------------------------------------------------------------------------
# TC-05: dogfood subprocess install（创建骨架 + stdout 断言 + 幂等）
# ---------------------------------------------------------------------------

def test_tc05_dogfood_subprocess_install(tmp_path, monkeypatch):
    """TC-05: subprocess 跑 harness install，断言路书骨架创建 + stdout 含 matched + 幂等。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _setup_git(tmp_path)

    # 模拟 harness-workflow 自身结构（src/{pkg}/{tools,playbook,assets}）
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "harness_workflow"\nversion = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "src" / "harness_workflow" / "tools").mkdir(parents=True)
    (tmp_path / "src" / "harness_workflow" / "playbook").mkdir(parents=True)
    (tmp_path / "src" / "harness_workflow" / "assets").mkdir(parents=True)

    result = _run_cli(tmp_path)
    combined_output = result.stdout + result.stderr

    # 路书骨架应该存在
    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX
    assert playbook_dir.exists(), f"playbook dir not created; stdout={result.stdout}, stderr={result.stderr}"
    assert (playbook_dir / "overview.md").exists()
    assert (playbook_dir / "architecture.md").exists()
    assert (playbook_dir / "runbook.md").exists()
    assert (playbook_dir / "code-map.md").exists()

    # domains/ 至少 1 个子目录
    domains_dir = playbook_dir / "domains"
    assert domains_dir.exists()
    domain_subdirs = [d for d in domains_dir.iterdir() if d.is_dir()]
    assert len(domain_subdirs) >= 1, "domains/ should have ≥ 1 subdirectory"

    # stdout 含 matched（domain inference 命中）
    assert "matched" in combined_output, f"Expected 'matched' in output: {combined_output}"

    # 第二次跑（幂等）：playbook 已存在，不覆盖（mtime 不变）
    mtime_before = (playbook_dir / "overview.md").stat().st_mtime
    result2 = _run_cli(tmp_path)
    assert (playbook_dir / "overview.md").exists()
    mtime_after = (playbook_dir / "overview.md").stat().st_mtime
    assert mtime_before == mtime_after, "Idempotency violated: overview.md was overwritten"
    assert "playbook 已存在" in result2.stdout or "playbook 已存在" in result2.stderr


# ---------------------------------------------------------------------------
# TC-06: install 默认装路书骨架（chg-D：不需要任何 flag 就装路书）
# ---------------------------------------------------------------------------

def test_tc06_install_always_creates_playbook(tmp_path, monkeypatch):
    """TC-06 (chg-D): install 始终创建路书骨架（无任何 flag）。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _setup_git(tmp_path)

    # 建 harness-workflow 自身结构（src/{pkg}/{tools,playbook,assets}）确保推断成功
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "harness_workflow"\nversion = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "src" / "harness_workflow" / "tools").mkdir(parents=True)
    (tmp_path / "src" / "harness_workflow" / "playbook").mkdir(parents=True)
    (tmp_path / "src" / "harness_workflow" / "assets").mkdir(parents=True)

    result = _run_cli(tmp_path)

    # 路书骨架应该存在
    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX
    assert playbook_dir.exists(), (
        f"playbook dir should always be created; stdout={result.stdout}, stderr={result.stderr}"
    )
    assert (playbook_dir / "overview.md").exists()
    assert (playbook_dir / "architecture.md").exists()


# ---------------------------------------------------------------------------
# TC-07: install 不输出 [ASSISTANT INSTRUCTION]（chg-D：提示句移到 refresh）
# ---------------------------------------------------------------------------

def test_tc07_install_no_assistant_instruction_output(tmp_path, monkeypatch):
    """TC-07 (chg-D): install 不输出 [ASSISTANT INSTRUCTION]；提示句改由 refresh 触发。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _setup_git(tmp_path)

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "harness_workflow"\nversion = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "src" / "harness_workflow" / "tools").mkdir(parents=True)
    (tmp_path / "src" / "harness_workflow" / "playbook").mkdir(parents=True)
    (tmp_path / "src" / "harness_workflow" / "assets").mkdir(parents=True)

    result = _run_cli(tmp_path)

    combined = result.stdout + result.stderr
    assert "[ASSISTANT INSTRUCTION" not in combined, (
        f"install should NOT output [ASSISTANT INSTRUCTION]; combined={combined}"
    )


# ---------------------------------------------------------------------------
# TC-08: install --no-llm 不输出 [ASSISTANT INSTRUCTION]（chg-D）
# ---------------------------------------------------------------------------

def test_tc08_install_no_llm_no_assistant_instruction(tmp_path, monkeypatch):
    """TC-08 (chg-D): install --no-llm 也不输出 [ASSISTANT INSTRUCTION]。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _setup_git(tmp_path)

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "harness_workflow"\nversion = "0.1.0"\n', encoding="utf-8")
    (tmp_path / "src" / "harness_workflow" / "tools").mkdir(parents=True)
    (tmp_path / "src" / "harness_workflow" / "playbook").mkdir(parents=True)
    (tmp_path / "src" / "harness_workflow" / "assets").mkdir(parents=True)

    result = _run_cli(tmp_path, "--no-llm")

    combined = result.stdout + result.stderr
    assert "[ASSISTANT INSTRUCTION" not in combined, (
        f"install --no-llm should NOT output [ASSISTANT INSTRUCTION]; combined={combined}"
    )
    # 路书骨架仍然存在
    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX
    assert playbook_dir.exists(), f"playbook dir should exist even with --no-llm; stdout={result.stdout}"


# ---------------------------------------------------------------------------
# TC-09: render_skeleton 4 顶层文件存在
# ---------------------------------------------------------------------------

def test_tc09_render_skeleton_top_files(tmp_path):
    """TC-09: render_skeleton 创建 4 顶层文件 + AUTO 区段存在。"""
    domains = ["core", "api"]
    written = render_skeleton(tmp_path, domains)

    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX
    top_files = ["overview.md", "architecture.md", "runbook.md", "code-map.md"]
    for fname in top_files:
        fpath = playbook_dir / fname
        assert fpath.exists(), f"{fname} should exist"

    # 检查 AUTO 区段存在
    arch_content = (playbook_dir / "architecture.md").read_text(encoding="utf-8")
    assert "<!-- AUTO:STACK -->" in arch_content
    assert "<!-- /AUTO:STACK -->" in arch_content
    assert "<!-- AUTO:LAYOUT -->" in arch_content
    assert "<!-- AUTO:SCRIPTS -->" in arch_content

    overview_content = (playbook_dir / "overview.md").read_text(encoding="utf-8")
    assert "<!-- AUTO:DOMAIN_LIST -->" in overview_content

    code_map_content = (playbook_dir / "code-map.md").read_text(encoding="utf-8")
    assert "<!-- AUTO:DOMAIN_FILES -->" in code_map_content

    assert written == len(top_files) + len(domains) * 4  # 4 顶层 + 每领域 4 件套


# ---------------------------------------------------------------------------
# TC-10: render_skeleton domains 4 件套存在
# ---------------------------------------------------------------------------

def test_tc10_render_skeleton_domain_files(tmp_path):
    """TC-10: render_skeleton 创建 domains/{name}/ 4 件套（README / code / data-model / notes）。"""
    domains = ["auth", "payment"]
    render_skeleton(tmp_path, domains)

    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX
    domain_files = ["README.md", "code.md", "data-model.md", "notes.md"]

    for domain in domains:
        domain_dir = playbook_dir / "domains" / domain
        assert domain_dir.exists(), f"domains/{domain}/ should exist"
        for fname in domain_files:
            fpath = domain_dir / fname
            assert fpath.exists(), f"domains/{domain}/{fname} should exist"

        # code.md 含 AUTO:DOMAIN_FILES 区段
        code_md = (domain_dir / "code.md").read_text(encoding="utf-8")
        assert "<!-- AUTO:DOMAIN_FILES -->" in code_md
        assert "<!-- /AUTO:DOMAIN_FILES -->" in code_md

        # README.md 含领域名
        readme = (domain_dir / "README.md").read_text(encoding="utf-8")
        assert domain in readme
