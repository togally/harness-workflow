"""tests/test_ignore_build_artifacts.py

chg-C Step 4.2：忽略构建产物目录，防止污染路书。

TC-01 _scan_domain_files 跳过 target/ 目录
TC-02 _scan_domain_files 跳过 node_modules / __pycache__ / build / dist
TC-03 真实 maven fixture（含 target/）跑后 AUTO:DOMAIN_FILES 不含 target/ 路径
TC-04 AUTO:LAYOUT 生成时不列 logs / target / build 等构建产物目录
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from harness_workflow.tools.harness_playbook_refresh import (
    _scan_domain_files,
    _scan_layout,
    IGNORE_DIRS,
    playbook_refresh,
)
from harness_workflow.playbook.skeleton import render_skeleton, PLAYBOOK_ROOT_SUFFIX


# ---------------------------------------------------------------------------
# TC-01: _scan_domain_files 跳过 target/ 目录
# ---------------------------------------------------------------------------

def test_tc01_scan_domain_files_skips_target(tmp_path):
    """TC-01: _scan_domain_files 不列出 target/ 目录下的 .java 文件。"""
    # 创建 maven 项目结构：order/ 模块含 src/main/java 源码 + target/ 构建产物
    domain_dir = tmp_path / "order"
    domain_dir.mkdir()

    # 真实源码
    src_main = domain_dir / "src" / "main" / "java" / "com" / "example" / "order"
    src_main.mkdir(parents=True)
    (src_main / "OrderService.java").write_text("public class OrderService {}", encoding="utf-8")

    # target/ 构建产物（不应出现在路书中）
    target_dir = domain_dir / "target" / "classes" / "com" / "example" / "order"
    target_dir.mkdir(parents=True)
    (target_dir / "OrderService.class").write_text("binary", encoding="utf-8")
    # 也放一个 .java 文件在 target/（某些构建工具可能这样）
    (target_dir / "OrderService.java").write_text("generated", encoding="utf-8")

    result = _scan_domain_files(domain_dir, tmp_path, "order")

    # target/ 下的文件不应出现
    assert "target/" not in result, (
        f"_scan_domain_files should not include files under target/, got:\n{result}"
    )
    # 真实源码应出现
    assert "OrderService.java" in result, (
        f"_scan_domain_files should include source files under src/, got:\n{result}"
    )
    # 确认 target 下的 java 没有
    lines = [l for l in result.splitlines() if "target" in l]
    assert len(lines) == 0, (
        f"Expected 0 lines with 'target' in output, got {len(lines)}: {lines}"
    )


# ---------------------------------------------------------------------------
# TC-02: _scan_domain_files 跳过 node_modules / __pycache__ / build / dist
# ---------------------------------------------------------------------------

def test_tc02_scan_domain_files_skips_build_dirs(tmp_path):
    """TC-02: _scan_domain_files 跳过 node_modules / __pycache__ / build / dist 目录。"""
    domain_dir = tmp_path / "frontend"
    domain_dir.mkdir()

    # 真实源码
    src_dir = domain_dir / "src"
    src_dir.mkdir()
    (src_dir / "App.tsx").write_text("export default function App() {}", encoding="utf-8")

    # 构建产物目录
    noise_dirs = ["node_modules", "__pycache__", "build", "dist"]
    for nd in noise_dirs:
        noise_path = domain_dir / nd
        noise_path.mkdir()
        (noise_path / "index.js").write_text("// generated", encoding="utf-8")
        (noise_path / "bundle.ts").write_text("// generated", encoding="utf-8")

    result = _scan_domain_files(domain_dir, tmp_path, "frontend")

    # 构建产物目录不应出现
    for nd in noise_dirs:
        assert f"{nd}/" not in result, (
            f"_scan_domain_files should not include files under {nd}/, got:\n{result}"
        )
    # 真实源码应出现
    assert "App.tsx" in result, (
        f"_scan_domain_files should include source files under src/, got:\n{result}"
    )


# ---------------------------------------------------------------------------
# TC-03: maven fixture（含 target/）→ AUTO:DOMAIN_FILES 不含 target/ 路径
# ---------------------------------------------------------------------------

def test_tc03_maven_fixture_domain_files_no_target(tmp_path):
    """TC-03: 含 target/ 的 Maven 模块跑 playbook_refresh 后 AUTO:DOMAIN_FILES 不含 target/ 路径。"""
    # 创建模拟 Maven 项目根
    (tmp_path / "pom.xml").write_text(
        "<project><artifactId>order</artifactId></project>",
        encoding="utf-8",
    )

    # 创建 order/ 子模块
    order_dir = tmp_path / "order"
    order_dir.mkdir()
    (order_dir / "pom.xml").write_text(
        "<project><artifactId>order</artifactId></project>",
        encoding="utf-8",
    )

    # 真实 Java 源码
    src_main = order_dir / "src" / "main" / "java" / "com" / "example"
    src_main.mkdir(parents=True)
    (src_main / "OrderService.java").write_text("public class OrderService {}", encoding="utf-8")

    # target/ 构建产物（包含 .java）
    target_gen = order_dir / "target" / "generated-sources" / "com" / "example"
    target_gen.mkdir(parents=True)
    (target_gen / "GeneratedModel.java").write_text("// generated", encoding="utf-8")

    # 渲染骨架（指定 order 领域）
    render_skeleton(tmp_path, ["order"])
    playbook_refresh(tmp_path)

    # 读 domains/order/code.md 的 AUTO:DOMAIN_FILES 区段
    code_md = tmp_path / PLAYBOOK_ROOT_SUFFIX / "domains" / "order" / "code.md"
    assert code_md.exists(), f"code.md should exist at {code_md}"

    content = code_md.read_text(encoding="utf-8")
    # 提取 AUTO:DOMAIN_FILES 区段
    m = re.search(
        r"<!-- AUTO:DOMAIN_FILES -->(.*?)<!-- /AUTO:DOMAIN_FILES -->",
        content, re.DOTALL
    )
    assert m is not None, "code.md should have AUTO:DOMAIN_FILES section"
    domain_files_content = m.group(1)

    # target/ 不应出现
    assert "target/" not in domain_files_content, (
        f"AUTO:DOMAIN_FILES should not contain target/ paths, got:\n{domain_files_content}"
    )
    # GeneratedModel.java 不应出现
    assert "GeneratedModel" not in domain_files_content, (
        f"AUTO:DOMAIN_FILES should not contain generated files from target/, got:\n{domain_files_content}"
    )


# ---------------------------------------------------------------------------
# TC-04: AUTO:LAYOUT 生成时不列 logs / target / build 等构建产物目录
# ---------------------------------------------------------------------------

def test_tc04_scan_layout_excludes_build_dirs(tmp_path):
    """TC-04: _scan_layout 不列出 logs / target / build / node_modules 等构建产物目录。"""
    # 创建一些真实目录
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs").mkdir()

    # 创建构建产物目录（应被过滤）
    build_artifact_dirs = ["target", "build", "logs", "node_modules", "__pycache__", "dist"]
    for d in build_artifact_dirs:
        artifact_dir = tmp_path / d
        artifact_dir.mkdir()
        # 放一些文件让目录非空
        (artifact_dir / "dummy.txt").write_text("artifact", encoding="utf-8")

    result = _scan_layout(tmp_path)

    # 真实目录应出现
    assert "src/" in result, f"Expected 'src/' in layout, got:\n{result}"
    assert "tests/" in result, f"Expected 'tests/' in layout, got:\n{result}"

    # 构建产物目录不应出现
    for d in build_artifact_dirs:
        assert f"`{d}/`" not in result, (
            f"Expected '{d}/' to be excluded from layout, got:\n{result}"
        )


# ---------------------------------------------------------------------------
# TC-05: IGNORE_DIRS 列表包含必要目录
# ---------------------------------------------------------------------------

def test_tc05_ignore_dirs_contains_required():
    """TC-05: IGNORE_DIRS 集合包含 target / build / logs / node_modules 等必要目录。"""
    required = {"target", "build", "dist", "node_modules", "__pycache__", "logs"}
    for d in required:
        assert d in IGNORE_DIRS, (
            f"Expected '{d}' in IGNORE_DIRS, but it's missing. Current set: {IGNORE_DIRS}"
        )
