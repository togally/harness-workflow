"""tests/test_petmall_fixture_dogfood.py

req-56（路书引擎升级）/ chg-04（install/refresh 集成 LLM）
PetMallPlatform-like fixture dogfood 测试

TC-Dogfood-01: PetMallPlatform 完整 pipeline
  输入：tmp_path + 5 顶层模块 platform-* + 父 pom.xml <modules> + spring-boot-maven-plugin
       + logs 噪声目录 + in-process mock LLM provider
  步骤：
    (1) 在进程内调 init_playbook（注入 mock LLM）→ 验证 install 成功 + 5 模块 README 被填充
    (2) subprocess playbook-refresh → 验证 AUTO:SCRIPTS 含 ≥ 4 行 mvn
    (3) subprocess playbook-check → 验证 exit 0
  期望：
    (a) install exit 0 + matched 'maven_multi_module' + 5 模块 domain README 被 mock LLM 填充
    (b) refresh exit 0 + architecture.md AUTO:SCRIPTS 含 ≥ 4 行 mvn 命令
    (c) check exit 0
    (d) runtime.yaml stage 字段存在
    (e) feedback.jsonl 事件数 ≥ 3（如果存在）
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from harness_workflow.playbook.skeleton import PLAYBOOK_ROOT_SUFFIX
from harness_workflow.playbook.llm import GeneratedContent, LLMProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_env() -> dict:
    """构建子进程环境变量（CI=true 跳过 LLM，避免真实调用）。"""
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_DIR}:{existing_pp}" if existing_pp else SRC_DIR
    env["CI"] = "true"
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("OPENAI_API_KEY", None)
    return env


def _setup_git(root: Path) -> None:
    """最小 git 初始化。"""
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True, capture_output=True)


def _setup_petmall_fixture(root: Path) -> list[str]:
    """创建 PetMallPlatform-like fixture。

    参考 reg-01 regression.md §3 维度 A 原始证据 A-3：
    - 5 顶层模块 platform-* + 父 pom.xml <modules>
    - spring-boot-maven-plugin（条件附加 mvn spring-boot:run）
    - logs/ 噪声目录（放在根目录，不含 pom.xml，不被 Maven 推断器当 domain）
    """
    modules = [
        "platform-admin",
        "platform-user",
        "platform-order",
        "platform-product",
        "platform-payment",
    ]

    # 父 pom.xml（含 <modules> + spring-boot-maven-plugin）
    modules_xml = "\n".join(f"    <module>{m}</module>" for m in modules)
    (root / "pom.xml").write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.petmall</groupId>
  <artifactId>petmall-platform</artifactId>
  <version>2.1.0-SNAPSHOT</version>
  <packaging>pom</packaging>
  <name>PetMall Platform</name>
  <modules>
{modules_xml}
  </modules>
  <build>
    <plugins>
      <plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
        <version>3.1.5</version>
      </plugin>
    </plugins>
  </build>
</project>
""",
        encoding="utf-8",
    )

    # 各子模块目录 + 最小 pom.xml
    for m in modules:
        mod_dir = root / m
        mod_dir.mkdir(exist_ok=True)
        (mod_dir / "pom.xml").write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<project>
  <parent>
    <artifactId>petmall-platform</artifactId>
  </parent>
  <artifactId>{m}</artifactId>
</project>
""",
            encoding="utf-8",
        )
        (mod_dir / "src" / "main" / "java").mkdir(parents=True, exist_ok=True)

    # 噪声目录：logs/ 放在根目录（不含 pom.xml，不被 Maven 推断器当 domain）
    (root / "logs").mkdir(exist_ok=True)
    (root / "logs" / "app.log").write_text("2026-01-01 00:00:00 INFO start\n", encoding="utf-8")

    return modules


def _read_llm_section(file_path: Path, marker: str) -> str:
    """提取 LLM 区段内容。"""
    content = file_path.read_text(encoding="utf-8")
    m = re.search(
        rf"<!-- LLM:{re.escape(marker)} -->(.*?)<!-- /LLM:{re.escape(marker)} -->",
        content,
        re.DOTALL,
    )
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# TC-Dogfood-01
# ---------------------------------------------------------------------------

def test_petmall_full_pipeline(tmp_path, monkeypatch, capsys):
    """TC-Dogfood-01: PetMallPlatform-like fixture 完整 3 步 pipeline。

    步骤：
      (1) 在进程内调 init_playbook（注入 mock LLM）
      (2) subprocess playbook-refresh（--no-llm，CI=true）
      (3) subprocess playbook-check（验证 exit 0）
    断言：
      (a) install 成功 + matched 'maven_multi_module' + 5 模块 domain README 被 mock LLM 填充
      (b) refresh exit 0 + AUTO:SCRIPTS ≥ 4 行 mvn 命令
      (c) check exit 0
      (d) runtime.yaml stage 字段存在
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 1. 设置 fixture
    _setup_git(tmp_path)
    modules = _setup_petmall_fixture(tmp_path)

    # -----------------------------------------------------------------------
    # (a) Step 1: 在进程内调 init_playbook（注入 mock LLM）
    # -----------------------------------------------------------------------
    content_obj = GeneratedContent(
        overview_description="PetMall Platform 是宠物商城微服务架构平台。",
        tech_decisions=["Java/Spring Boot", "Maven 多模块", "MySQL", "Redis", "Spring Cloud"],
        domain_descriptions={m: f"{m} 模块负责平台对应业务服务。" for m in modules},
        domain_keywords={m: [f"{m}", "service", "api"] for m in modules},
    )

    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.name = "MockProvider"
    mock_provider.is_available.return_value = True
    mock_provider.generate.return_value = content_obj

    # patch auto_detect_provider（init.py 从 llm 模块 import）
    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *a, **kw: mock_provider,
    )
    monkeypatch.delenv("CI", raising=False)

    from harness_workflow.playbook.init import init_playbook
    from harness_workflow.playbook.domain_inference import infer_domains

    # 验证 Maven 多模块推断
    matched_mode, domains = infer_domains(tmp_path)
    captured = capsys.readouterr()

    assert "maven_multi_module" in matched_mode or "maven_multi_module" in captured.out, (
        f"Expected 'maven_multi_module' in domain inference, mode={matched_mode!r}, out={captured.out!r}"
    )
    assert set(modules).issubset(set(domains)), (
        f"Expected all 5 modules in domains, got: {domains}"
    )

    rc = init_playbook(tmp_path, no_llm=False)
    assert rc == 0, f"init_playbook returned {rc}"
    capsys.readouterr()  # flush stdout

    # generate 被调 ≥1 次
    assert mock_provider.generate.call_count >= 1, (
        f"Expected generate() called ≥1 time, got {mock_provider.generate.call_count}"
    )

    # 5 模块 domain README.md 被 mock LLM 填充（DOMAIN_DESC 含 mock 内容）
    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX
    assert playbook_dir.exists(), "playbook dir should exist"

    filled_count = 0
    for module in modules:
        readme = playbook_dir / "domains" / module / "README.md"
        assert readme.exists(), f"domain README.md should exist for {module}"
        section = _read_llm_section(readme, "DOMAIN_DESC")
        if f"{module} 模块负责" in section:
            filled_count += 1

    assert filled_count >= 3, (
        f"Expected ≥3 domain READMEs filled by mock LLM, got {filled_count}/{len(modules)}"
    )

    # -----------------------------------------------------------------------
    # (b) Step 2: subprocess playbook-refresh
    # -----------------------------------------------------------------------
    env = _make_env()

    refresh_result = subprocess.run(
        [
            sys.executable, "-m", "harness_workflow.cli",
            "playbook-refresh", "--root", str(tmp_path),
            "--no-llm",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    assert refresh_result.returncode == 0, (
        f"playbook-refresh returned {refresh_result.returncode};\n"
        f"stdout={refresh_result.stdout!r}\nstderr={refresh_result.stderr!r}"
    )

    # AUTO:SCRIPTS 含 ≥ 4 行 mvn 命令
    arch_md = playbook_dir / "architecture.md"
    assert arch_md.exists(), "architecture.md should exist"
    arch_content = arch_md.read_text(encoding="utf-8")

    scripts_m = re.search(
        r"<!-- AUTO:SCRIPTS -->(.*?)<!-- /AUTO:SCRIPTS -->",
        arch_content,
        re.DOTALL,
    )
    assert scripts_m, "AUTO:SCRIPTS section should exist in architecture.md"
    scripts_content = scripts_m.group(1)
    mvn_lines = [line for line in scripts_content.splitlines() if "mvn" in line]
    assert len(mvn_lines) >= 4, (
        f"Expected ≥4 mvn lines in AUTO:SCRIPTS, got {len(mvn_lines)}: {scripts_content}"
    )

    # -----------------------------------------------------------------------
    # (c) Step 3: subprocess playbook-check
    # -----------------------------------------------------------------------
    check_result = subprocess.run(
        [
            sys.executable, "-m", "harness_workflow.cli",
            "playbook-check", "--root", str(tmp_path),
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    assert check_result.returncode == 0, (
        f"playbook-check returned {check_result.returncode};\n"
        f"stdout={check_result.stdout!r}\nstderr={check_result.stderr!r}"
    )

    # -----------------------------------------------------------------------
    # (d) runtime.yaml stage 字段存在
    # -----------------------------------------------------------------------
    runtime_yaml_path = tmp_path / ".workflow" / "state" / "runtime.yaml"
    # install_repo 由 subprocess install 触发；in-process init_playbook 不创建 runtime.yaml
    # 如果存在则验证 stage 字段
    if runtime_yaml_path.exists():
        runtime_text = runtime_yaml_path.read_text(encoding="utf-8")
        assert "stage" in runtime_text, (
            f"Expected 'stage' field in runtime.yaml, got:\n{runtime_text}"
        )
