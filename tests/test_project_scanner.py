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
