"""tests/test_playbook_refresh_dogfood_multi_lang.py

req-56（路书引擎升级——Java/Maven + LLM + 区段级只读）/ chg-02（SCRIPTS detector 注册化）
dogfood TC：subprocess 调 CLI playbook-refresh + Maven fixture + 断言 AUTO:SCRIPTS 区段含 mvn 命令。

TC-Dogfood-01: tmp_path + 完整路书骨架（runbook.md 含 AUTO:SCRIPTS） + pom.xml fixture
    + subprocess python3 -m harness_workflow.cli playbook-refresh --root <tmp>
    → exit 0 + AUTO:SCRIPTS 区段含 ≥ 4 行 mvn 命令
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
sys.path.insert(0, SRC_DIR)

from harness_workflow.playbook.skeleton import render_skeleton, PLAYBOOK_ROOT_SUFFIX


def test_maven_refresh_dogfood(tmp_path, monkeypatch):
    """TC-Dogfood-01: subprocess 调 CLI playbook-refresh + Maven pom.xml → exit 0 + AUTO:SCRIPTS 含 ≥ 4 行 mvn 命令。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 1. 创建完整路书骨架
    render_skeleton(tmp_path, ["core", "order"])

    # 2. 写入 Maven pom.xml（含 spring-boot-maven-plugin）
    (tmp_path / "pom.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>spring-demo</artifactId>
  <version>1.0.0</version>
  <packaging>jar</packaging>
  <build>
    <plugins>
      <plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
        <version>3.1.0</version>
      </plugin>
    </plugins>
  </build>
</project>
""",
        encoding="utf-8",
    )

    # 3. subprocess 调 CLI
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_DIR}:{existing_pythonpath}" if existing_pythonpath else SRC_DIR

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "harness_workflow.cli",
            "playbook-refresh",
            "--root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    # 4. 断言 exit 0
    assert result.returncode == 0, (
        f"playbook-refresh returned {result.returncode}; "
        f"stdout={result.stdout}; stderr={result.stderr}"
    )

    # 5. 读 architecture.md AUTO:SCRIPTS 区段
    arch_md = tmp_path / PLAYBOOK_ROOT_SUFFIX / "architecture.md"
    assert arch_md.exists(), "architecture.md 不存在"
    arch_content = arch_md.read_text(encoding="utf-8")

    scripts_m = re.search(
        r"<!-- AUTO:SCRIPTS -->(.*?)<!-- /AUTO:SCRIPTS -->",
        arch_content,
        re.DOTALL,
    )
    assert scripts_m, "AUTO:SCRIPTS 区段不存在"
    scripts_content = scripts_m.group(1)

    # 断言含 ≥ 4 行 mvn 命令
    mvn_lines = [line for line in scripts_content.splitlines() if "mvn" in line]
    assert len(mvn_lines) >= 4, (
        f"AUTO:SCRIPTS 区段含 {len(mvn_lines)} 行 mvn 命令（预期 ≥ 4）: {scripts_content}"
    )

    assert "mvn clean install" in scripts_content, f"缺少 mvn clean install: {scripts_content}"
    assert "mvn test" in scripts_content, f"缺少 mvn test: {scripts_content}"
    assert "mvn package" in scripts_content, f"缺少 mvn package: {scripts_content}"
    assert "mvn spring-boot:run" in scripts_content, f"缺少 mvn spring-boot:run: {scripts_content}"

    # 6. stdout/stderr 含刷新相关输出
    combined = result.stdout + result.stderr
    assert "refresh" in combined.lower() or "刷新" in combined or "已是最新" in combined, (
        f"stdout 未含 refresh 相关输出: {combined}"
    )
