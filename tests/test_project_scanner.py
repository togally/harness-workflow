"""req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-01（项目描述扫描器 + project-profile 落地）

覆盖：
- Step 1：pyproject.toml / package.json 解析
- Step 2：pom.xml / go.mod / Cargo.toml / README / CLAUDE / AGENTS
- Step 3：render_project_profile 渲染 + content_hash + generated_at
- Step 4：load_project_profile 反向解析 + 空仓兜底

严格遵循 TDD 红绿纪律；时间戳/hash 通过依赖注入 mock。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


# -----------------------------
# Step 1: 骨架 + pyproject / package.json
# -----------------------------

def test_scan_python_poetry_project(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 1：pyproject.toml 解析最小用例。"""
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "demo-app"
version = "0.1.0"
description = "Sample"
dependencies = ["requests>=2.0", "click>=8"]

[project.scripts]
demo = "demo.cli:main"
""".strip(),
        encoding="utf-8",
    )

    from harness_workflow.project_scanner import build_project_profile

    profile = build_project_profile(tmp_path)
    assert profile.package_name == "demo-app"
    assert profile.language == "python"
    assert "requests>=2.0" in profile.deps_top or "requests" in " ".join(profile.deps_top)
    assert any("demo" in ep for ep in profile.entrypoints)
    assert "python+pyproject" in profile.stack_tags


def test_scan_node_project(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 1：package.json 解析最小用例。"""
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "demo-node",
                "version": "1.2.3",
                "main": "index.js",
                "scripts": {"start": "node index.js"},
                "dependencies": {"express": "^4.18.0"},
                "devDependencies": {"typescript": "^5.0.0"},
            }
        ),
        encoding="utf-8",
    )

    from harness_workflow.project_scanner import build_project_profile

    profile = build_project_profile(tmp_path)
    assert profile.package_name == "demo-node"
    assert profile.language == "nodejs"
    joined = " ".join(profile.deps_top)
    assert "express" in joined
    assert any("start" in ep or "node index.js" in ep for ep in profile.entrypoints)
    # TS 存在应有 node+ts 标签
    assert "node+ts" in profile.stack_tags or "nodejs" in profile.stack_tags


# -----------------------------
# Step 2: 其余描述文件
# -----------------------------


def test_scan_maven_project(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 2：pom.xml 解析最小用例。"""
    (tmp_path / "pom.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>demo-java</artifactId>
  <version>0.1.0</version>
  <dependencies>
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-core</artifactId>
      <version>6.0.0</version>
    </dependency>
  </dependencies>
</project>
""".strip(),
        encoding="utf-8",
    )

    from harness_workflow.project_scanner import build_project_profile

    profile = build_project_profile(tmp_path)
    assert profile.package_name == "demo-java"
    assert profile.language == "java"
    assert any("spring-core" in dep for dep in profile.deps_top)
    assert "java+maven" in profile.stack_tags


def test_scan_go_module(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 2：go.mod 解析最小用例。"""
    (tmp_path / "go.mod").write_text(
        """
module github.com/acme/demo-go

go 1.21

require (
    github.com/gorilla/mux v1.8.0
    github.com/stretchr/testify v1.8.4
)
""".strip(),
        encoding="utf-8",
    )

    from harness_workflow.project_scanner import build_project_profile

    profile = build_project_profile(tmp_path)
    assert profile.package_name == "demo-go"
    assert profile.language == "go"
    assert any("gorilla/mux" in dep for dep in profile.deps_top)
    assert "go-module" in profile.stack_tags


def test_scan_rust_cargo_project(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 2：Cargo.toml 解析最小用例。"""
    (tmp_path / "Cargo.toml").write_text(
        """
[package]
name = "demo-rust"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = "1.0"
tokio = { version = "1", features = ["full"] }
""".strip(),
        encoding="utf-8",
    )

    from harness_workflow.project_scanner import build_project_profile

    profile = build_project_profile(tmp_path)
    assert profile.package_name == "demo-rust"
    assert profile.language == "rust"
    joined = " ".join(profile.deps_top)
    assert "serde" in joined and "tokio" in joined
    assert "rust-cargo" in profile.stack_tags


def test_scan_readme_headline(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 2：README.md 首 H1 作为 project_headline。"""
    (tmp_path / "README.md").write_text(
        "# My Cool Project\n\nSome description.\n", encoding="utf-8"
    )

    from harness_workflow.project_scanner import build_project_profile

    profile = build_project_profile(tmp_path)
    assert profile.project_headline == "My Cool Project"


def test_scan_claude_md_headline(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 2：CLAUDE.md 首 H1 兜底作为 project_headline。"""
    (tmp_path / "CLAUDE.md").write_text(
        "# Claude Project Guide\n\nusage notes\n", encoding="utf-8"
    )

    from harness_workflow.project_scanner import build_project_profile

    profile = build_project_profile(tmp_path)
    assert profile.project_headline == "Claude Project Guide"


def test_scan_agents_md_headline(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 2：AGENTS.md 首 H1 兜底作为 project_headline。"""
    (tmp_path / "AGENTS.md").write_text(
        "# Agents Manifest\n", encoding="utf-8"
    )

    from harness_workflow.project_scanner import build_project_profile

    profile = build_project_profile(tmp_path)
    assert profile.project_headline == "Agents Manifest"


# -----------------------------
# Step 3: render_project_profile 渲染 + 时间戳 + content_hash
# -----------------------------


def _fixed_now() -> datetime:
    return datetime(2026, 4, 21, 12, 0, 0, tzinfo=timezone.utc)


def test_render_project_profile_snapshot(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 3：固定输入 → 固定结构断言（frontmatter + 三段）。"""
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "snap-demo"
dependencies = ["requests>=2.0"]
""".strip(),
        encoding="utf-8",
    )

    from harness_workflow.project_scanner import (
        build_project_profile,
        render_project_profile,
    )

    profile = build_project_profile(tmp_path)
    text = render_project_profile(profile, now=_fixed_now)

    assert text.startswith("---"), "应以 YAML frontmatter 起始"
    assert "generated_at: 2026-04-21T12:00:00+00:00" in text
    assert "content_hash:" in text
    assert "## 结构化字段" in text
    assert "## 项目用途（LLM 填充）" in text
    assert "## 项目规范（LLM 填充）" in text
    assert "snap-demo" in text


def test_hash_stable_across_renders(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 3：相同输入 + 相同时间 → content_hash 稳定。"""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'stable-demo'\n", encoding="utf-8"
    )

    from harness_workflow.project_scanner import (
        build_project_profile,
        render_project_profile,
    )

    profile = build_project_profile(tmp_path)
    text_a = render_project_profile(profile, now=_fixed_now)
    text_b = render_project_profile(profile, now=_fixed_now)
    assert text_a == text_b

    # 正文内容变化时 hash 应变；通过字段对比间接验证
    import re as _re

    hash_a = _re.search(r"content_hash:\s*(\S+)", text_a).group(1)
    profile.package_name = "stable-demo-v2"
    text_c = render_project_profile(profile, now=_fixed_now)
    hash_c = _re.search(r"content_hash:\s*(\S+)", text_c).group(1)
    assert hash_a != hash_c


# -----------------------------
# Step 4: load_project_profile 反向解析 + 空仓兜底 + write_project_profile
# -----------------------------


def test_load_round_trip(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 4：render → load 字段往返一致。"""
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "roundtrip-demo"
dependencies = ["click>=8", "rich>=13"]
""".strip(),
        encoding="utf-8",
    )

    from harness_workflow.project_scanner import (
        build_project_profile,
        load_project_profile,
        render_project_profile,
    )

    profile = build_project_profile(tmp_path)
    text = render_project_profile(profile, now=_fixed_now)
    target = tmp_path / "profile.md"
    target.write_text(text, encoding="utf-8")

    loaded = load_project_profile(target)
    assert loaded is not None
    assert loaded.package_name == "roundtrip-demo"
    assert loaded.language == "python"
    assert any("click" in dep for dep in loaded.deps_top)


def test_empty_repo_profile(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 4：空目录兜底 → profile 字段为空但 section 完整。"""
    from harness_workflow.project_scanner import (
        build_project_profile,
        render_project_profile,
    )

    profile = build_project_profile(tmp_path)
    assert profile.language == "unknown"
    assert profile.package_name == ""
    assert profile.deps_top == []
    assert profile.stack_tags == []

    text = render_project_profile(profile, now=_fixed_now)
    assert "## 结构化字段" in text
    assert "## 项目用途（LLM 填充）" in text
    assert "## 项目规范（LLM 填充）" in text
    assert "content_hash:" in text


def test_write_project_profile_entrypoint(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 4：write_project_profile 顶层入口写盘 + 回读对比 hash。"""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'write-demo'\n", encoding="utf-8"
    )

    from harness_workflow.project_scanner import (
        PROFILE_REL_PATH,
        load_project_profile,
        write_project_profile,
    )

    written = write_project_profile(tmp_path)
    assert written == tmp_path / PROFILE_REL_PATH
    assert written.exists()
    assert written.read_text(encoding="utf-8").startswith("---")

    loaded = load_project_profile(written)
    assert loaded is not None
    assert loaded.package_name == "write-demo"


def test_load_missing_file_returns_none(tmp_path: Path) -> None:
    """req-32 / chg-01 / Step 4：不存在文件 → load 返回 None（不抛）。"""
    from harness_workflow.project_scanner import load_project_profile

    assert load_project_profile(tmp_path / "nowhere.md") is None
