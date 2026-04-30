"""tests/test_playbook_check.py

req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-05（harness playbook-check 子命令）
pytest 测试套件（≥ 11 TC）

TC-01: D-01 依赖漂移（新 dep 未提及 architecture.md AUTO:STACK）
TC-02: D-02 scripts 漂移（新 script 未提及 architecture.md AUTO:SCRIPTS）
TC-03: D-03 模块目录漂移（新 src/{pkg}/foo/ 无 domains/foo/）
TC-04: D-04 code-map 互引漂移（domains/auth/ 存在但 code-map.md 无登记）
TC-05: D-05 code.md 引用失效（code.md 引用不存在文件）
TC-06: D-06 README 依赖链接失效（依赖: nonexistent 目录不存在）
TC-07: K-01 关键词为空（README.md ## 职责描述 仅 TODO）
TC-08: OQ-5 关键 TC：AUTO 区段哈希漂移（手改 AUTO 段）
TC-09: 健康仓库 exit 0
TC-10: dogfood subprocess（subprocess 调 CLI playbook-check）
TC-11: harness validate --contract playbook-layout 集成
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
sys.path.insert(0, SRC_DIR)

from harness_workflow.tools.harness_playbook_check import (
    playbook_check,
    check_d01_dependency_drift,
    check_d02_scripts_drift,
    check_d03_module_dir_drift,
    check_d04_codemap_consistency,
    check_d05_codefile_path_validity,
    check_d06_readme_dep_link,
    check_k01_keyword_coverage,
    check_c01_auto_segment_pairs,
    check_c03_path_schema,
    check_c05_domain_consistency,
    check_auto_segment_hash_drift,
    PLAYBOOK_ROOT_SUFFIX,
)
from harness_workflow.playbook.skeleton import render_skeleton
from harness_workflow.tools.harness_playbook_refresh import playbook_refresh


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_playbook(root: Path, domains: list[str] | None = None) -> Path:
    """在 tmp_path 中创建路书骨架并执行 refresh（使 AUTO 区段内容与期望一致）。"""
    if domains is None:
        domains = []
    render_skeleton(root, domains)
    playbook_refresh(root)
    return root / PLAYBOOK_ROOT_SUFFIX


def _make_healthy_playbook(tmp_path: Path) -> Path:
    """创建健康状态路书（无漂移）。"""
    playbook_dir = _make_playbook(tmp_path, domains=["core"])
    # 确保 core/README.md 有真实职责描述（≥ 11 字节，非 TODO）
    readme = playbook_dir / "domains" / "core" / "README.md"
    content = readme.read_text(encoding="utf-8")
    content = content.replace(
        "<!-- TODO: ≤ 3 句描述该领域处理什么业务 -->",
        "核心业务逻辑模块，负责系统核心流程处理。"
    )
    readme.write_text(content, encoding="utf-8")
    return playbook_dir


# ---------------------------------------------------------------------------
# TC-01: D-01 依赖漂移
# ---------------------------------------------------------------------------

def test_tc01_d01_dependency_drift(tmp_path, capsys):
    """TC-01: 新 dep 'newlibrary' 在 pyproject.toml 但 AUTO:STACK 未提及 → exit 1 + 含 'dependency drift'。"""
    playbook_dir = _make_playbook(tmp_path)

    # 写入 pyproject.toml，含新 dep 'newlibrary'
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "testapp"\n[project.dependencies]\nnewlibrary = ">=1.0"\n',
        encoding="utf-8",
    )

    # AUTO:STACK 刷新后只含 newlibrary 如果真的运行过 refresh 才有；
    # 此时手动把 STACK 区段内容清空（模拟 dep 新增但区段未更新）
    arch_md = playbook_dir / "architecture.md"
    content = arch_md.read_text(encoding="utf-8")
    content = content.replace("<!-- AUTO:STACK -->\n", "<!-- AUTO:STACK -->\n")
    # 替换 STACK 区段为空内容（不含 newlibrary）
    import re
    content = re.sub(
        r"<!-- AUTO:STACK -->.*?<!-- /AUTO:STACK -->",
        "<!-- AUTO:STACK -->\n- Python (pyproject.toml)\n<!-- /AUTO:STACK -->",
        content, flags=re.DOTALL
    )
    arch_md.write_text(content, encoding="utf-8")

    result = check_d01_dependency_drift(tmp_path, playbook_dir)
    assert not result.passed
    assert any("dependency drift" in issue.lower() or "D-01" in issue for issue in result.issues)

    # 全量 check 返回 exit 1
    rc = playbook_check(tmp_path)
    captured = capsys.readouterr()
    assert rc == 1
    assert "dependency drift" in captured.out.lower() or "d-01" in captured.out.lower()


# ---------------------------------------------------------------------------
# TC-02: D-02 scripts 漂移
# ---------------------------------------------------------------------------

def test_tc02_d02_scripts_drift(tmp_path, capsys):
    """TC-02: Makefile 新 target 'deploy' 未在 AUTO:SCRIPTS 中提及 → exit 1 + 含 'scripts drift'。"""
    playbook_dir = _make_playbook(tmp_path)

    # 写 Makefile
    (tmp_path / "Makefile").write_text(
        "deploy:\n\techo deploying\n\ntest:\n\tpytest\n",
        encoding="utf-8",
    )

    # 将 SCRIPTS 区段手动设为空（模拟脚本未刷新）
    arch_md = playbook_dir / "architecture.md"
    content = arch_md.read_text(encoding="utf-8")
    import re
    content = re.sub(
        r"<!-- AUTO:SCRIPTS -->.*?<!-- /AUTO:SCRIPTS -->",
        "<!-- AUTO:SCRIPTS -->\n<!-- 未检测到脚本配置 -->\n<!-- /AUTO:SCRIPTS -->",
        content, flags=re.DOTALL
    )
    arch_md.write_text(content, encoding="utf-8")

    result = check_d02_scripts_drift(tmp_path, playbook_dir)
    assert not result.passed
    assert any("scripts drift" in issue.lower() or "D-02" in issue for issue in result.issues)

    rc = playbook_check(tmp_path)
    captured = capsys.readouterr()
    assert rc == 1
    assert "scripts drift" in captured.out.lower() or "d-02" in captured.out.lower()


# ---------------------------------------------------------------------------
# TC-03: D-03 模块目录漂移
# ---------------------------------------------------------------------------

def test_tc03_d03_module_dir_drift(tmp_path, capsys):
    """TC-03: src/mypkg/newmod/ 存在但 domains/newmod/ 不存在 → exit 1。"""
    playbook_dir = _make_playbook(tmp_path, domains=["core"])

    # 创建源码模块目录
    (tmp_path / "src" / "mypkg" / "newmod").mkdir(parents=True, exist_ok=True)
    (tmp_path / "src" / "mypkg" / "newmod" / "__init__.py").write_text("", encoding="utf-8")

    result = check_d03_module_dir_drift(tmp_path, playbook_dir)
    assert not result.passed
    assert any("newmod" in issue for issue in result.issues)

    rc = playbook_check(tmp_path)
    assert rc == 1


# ---------------------------------------------------------------------------
# TC-04: D-04 code-map 互引漂移
# ---------------------------------------------------------------------------

def test_tc04_d04_codemap_ref_drift(tmp_path, capsys):
    """TC-04: domains/auth/ 存在但 code-map.md AUTO:DOMAIN_FILES 未登记 → exit 1。"""
    playbook_dir = _make_playbook(tmp_path, domains=["core"])

    # 直接创建 domains/auth/ 子目录（不通过 install 走 render_skeleton）
    auth_dir = playbook_dir / "domains" / "auth"
    auth_dir.mkdir(parents=True, exist_ok=True)
    (auth_dir / "README.md").write_text("# auth\n\n## 职责描述\n\n身份认证模块。\n", encoding="utf-8")

    # code-map.md 的 DOMAIN_FILES 区段只登记 core，不含 auth
    code_map_md = playbook_dir / "code-map.md"
    content = code_map_md.read_text(encoding="utf-8")
    import re
    # 确保 auth 不在 DOMAIN_FILES 区段
    content = re.sub(
        r"<!-- AUTO:DOMAIN_FILES -->.*?<!-- /AUTO:DOMAIN_FILES -->",
        "<!-- AUTO:DOMAIN_FILES -->\n### core\n<!-- core 暂无文件 -->\n\n<!-- /AUTO:DOMAIN_FILES -->",
        content, flags=re.DOTALL
    )
    code_map_md.write_text(content, encoding="utf-8")

    result = check_d04_codemap_consistency(tmp_path, playbook_dir)
    assert not result.passed
    assert any("auth" in issue for issue in result.issues)

    rc = playbook_check(tmp_path)
    assert rc == 1


# ---------------------------------------------------------------------------
# TC-05: D-05 code.md 引用失效
# ---------------------------------------------------------------------------

def test_tc05_d05_codefile_path_validity(tmp_path, capsys):
    """TC-05: code.md 引用 'src/nonexistent.py' 但文件不存在 → exit 1。"""
    playbook_dir = _make_playbook(tmp_path, domains=["core"])

    # 写入带失效引用的 code.md
    code_md = playbook_dir / "domains" / "core" / "code.md"
    code_md.write_text(
        "# 领域代码清单：core\n\n## 文件列表\n\n"
        "<!-- AUTO:DOMAIN_FILES -->\n"
        "- `src/nonexistent.py`: 不存在的文件\n"
        "<!-- /AUTO:DOMAIN_FILES -->\n",
        encoding="utf-8",
    )

    result = check_d05_codefile_path_validity(tmp_path, playbook_dir)
    assert not result.passed
    assert any("nonexistent.py" in issue for issue in result.issues)

    rc = playbook_check(tmp_path)
    assert rc == 1


# ---------------------------------------------------------------------------
# TC-06: D-06 README 依赖链接失效
# ---------------------------------------------------------------------------

def test_tc06_d06_readme_dep_link(tmp_path, capsys):
    """TC-06: README.md 依赖领域 'payment' 但 domains/payment/ 不存在 → exit 1。"""
    playbook_dir = _make_playbook(tmp_path, domains=["core"])

    readme = playbook_dir / "domains" / "core" / "README.md"
    readme.write_text(
        "# 领域：core\n\n## 领域名称\n\ncore\n\n## 职责描述\n\n核心业务逻辑。\n\n"
        "## 依赖领域\n\n依赖：payment\n",
        encoding="utf-8",
    )

    result = check_d06_readme_dep_link(tmp_path, playbook_dir)
    assert not result.passed
    assert any("payment" in issue for issue in result.issues)

    rc = playbook_check(tmp_path)
    assert rc == 1


# ---------------------------------------------------------------------------
# TC-07: K-01 关键词为空
# ---------------------------------------------------------------------------

def test_tc07_k01_keyword_coverage(tmp_path, capsys):
    """TC-07: README.md ## 职责描述 仅 TODO → exit 1 + 含 'empty keywords'。"""
    playbook_dir = _make_playbook(tmp_path, domains=["core"])

    # 默认骨架的 README.md 职责描述是 TODO，满足测试条件
    readme = playbook_dir / "domains" / "core" / "README.md"
    # 强制确保职责描述是 TODO
    content = readme.read_text(encoding="utf-8")
    import re
    content = re.sub(
        r"##\s*职责描述.*?(?=\n##|\Z)",
        "## 职责描述\n\n<!-- TODO: ≤ 3 句描述 -->",
        content, flags=re.DOTALL
    )
    readme.write_text(content, encoding="utf-8")

    result = check_k01_keyword_coverage(tmp_path, playbook_dir)
    assert not result.passed
    assert any("empty keywords" in issue.lower() or "K-01" in issue for issue in result.issues)

    rc = playbook_check(tmp_path)
    captured = capsys.readouterr()
    assert rc == 1
    assert "empty keywords" in captured.out.lower() or "k-01" in captured.out.lower()


# ---------------------------------------------------------------------------
# TC-08: OQ-5 关键 TC：AUTO 区段哈希漂移
# ---------------------------------------------------------------------------

def test_tc08_oq5_auto_segment_hash_drift(tmp_path, capsys):
    """TC-08 OQ-5 关键 TC: 手动修改 AUTO:STACK 区段内容（保留 marker 完整）
    但不跑 refresh → exit 1 + stdout 含 'AUTO segment drift detected'。"""
    playbook_dir = _make_playbook(tmp_path)

    # 创建 pyproject.toml（让 refresh 有确定性内容）
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myapp"\n[tool.poetry.dependencies]\nrequests = ">=2.0"\n',
        encoding="utf-8",
    )

    # 先跑 refresh，使区段内容与期望一致
    playbook_refresh(tmp_path)

    # 手动改 AUTO:STACK 区段内容（路书只读软约束被违反）
    arch_md = playbook_dir / "architecture.md"
    content = arch_md.read_text(encoding="utf-8")
    import re
    content = re.sub(
        r"(<!-- AUTO:STACK -->)(.*?)(<!-- /AUTO:STACK -->)",
        r"\1\nHAND_EDITED_CONTENT_THIS_IS_WRONG\n\3",
        content, flags=re.DOTALL
    )
    arch_md.write_text(content, encoding="utf-8")

    result = check_auto_segment_hash_drift(tmp_path, playbook_dir)
    assert not result.passed, f"Expected drift detection but passed. Issues: {result.issues}"
    assert any("AUTO segment drift" in issue for issue in result.issues)

    rc = playbook_check(tmp_path)
    captured = capsys.readouterr()
    assert rc == 1
    assert "AUTO segment drift detected" in captured.out, \
        f"Expected 'AUTO segment drift detected' in stdout:\n{captured.out}"


# ---------------------------------------------------------------------------
# TC-09: 健康仓库 exit 0
# ---------------------------------------------------------------------------

def test_tc09_healthy_playbook_exit0(tmp_path, capsys):
    """TC-09: 健康 fixture（install 后立即 refresh）→ exit 0 + stdout 含 'PASS: 0 drift'。"""
    playbook_dir = _make_healthy_playbook(tmp_path)

    rc = playbook_check(tmp_path)
    captured = capsys.readouterr()

    # 期望 0 或者仅有 D-03（因为没有实际 src/ 模块，健康状态下 D-03 应无漂移）
    # 健康 fixture 中 code-map 和 overview.md AUTO 区段内容应与 refresh 期望一致
    # K-01 已在 _make_healthy_playbook 中修复
    assert rc == 0, (
        f"Expected exit 0 but got {rc}.\nstdout:\n{captured.out}\nstderr:\n{captured.err}"
    )
    assert "PASS" in captured.out and ("0 drift" in captured.out or "no drift" in captured.out.lower())


# ---------------------------------------------------------------------------
# TC-10: dogfood subprocess
# ---------------------------------------------------------------------------

def test_tc10_dogfood_subprocess(tmp_path):
    """TC-10: subprocess 调 python -m harness_workflow.cli playbook-check --root <tmpdir>
    健康 fixture → exit 0。"""
    _make_healthy_playbook(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "playbook-check", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": SRC_DIR},
    )
    assert result.returncode == 0, (
        f"subprocess playbook-check returned {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "PASS" in result.stdout


# ---------------------------------------------------------------------------
# TC-11: harness validate --contract playbook-layout 集成
# ---------------------------------------------------------------------------

def test_tc11_validate_contract_playbook_layout(tmp_path):
    """TC-11: subprocess 调 validate --contract playbook-layout → exit 0（健康 fixture）。"""
    _make_healthy_playbook(tmp_path)

    result = subprocess.run(
        [
            sys.executable, "-m", "harness_workflow.cli",
            "validate", "--contract", "playbook-layout",
            "--root", str(tmp_path),
        ],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": SRC_DIR},
    )
    assert result.returncode == 0, (
        f"validate --contract playbook-layout returned {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "PASS" in result.stdout


# ---------------------------------------------------------------------------
# TC-12: C-01 AUTO 区段配对校验
# ---------------------------------------------------------------------------

def test_tc12_c01_auto_segment_unpaired(tmp_path, capsys):
    """TC-12: architecture.md 中 <!-- AUTO:STACK --> 存在但 <!-- /AUTO:STACK --> 缺失 → exit 1。"""
    playbook_dir = _make_playbook(tmp_path)

    arch_md = playbook_dir / "architecture.md"
    content = arch_md.read_text(encoding="utf-8")
    # 删除闭标记
    content = content.replace("<!-- /AUTO:STACK -->", "<!-- 已被手动删除 -->")
    arch_md.write_text(content, encoding="utf-8")

    result = check_c01_auto_segment_pairs(tmp_path, playbook_dir)
    assert not result.passed
    assert any("SEGMENT_UNPAIRED" in issue or "STACK" in issue for issue in result.issues)


# ---------------------------------------------------------------------------
# TC-13: no playbook dir → exit 0 (no drift)
# ---------------------------------------------------------------------------

def test_tc13_no_playbook_dir_exit0(tmp_path, capsys):
    """TC-13: playbook 目录不存在 → exit 0（无路书无漂移）。"""
    rc = playbook_check(tmp_path)
    captured = capsys.readouterr()
    assert rc == 0
    # stderr 应有 WARN
    assert "warn" in captured.err.lower() or "不存在" in captured.err
