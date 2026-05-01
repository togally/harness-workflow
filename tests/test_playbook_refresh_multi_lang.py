"""tests/test_playbook_refresh_multi_lang.py

req-56（路书引擎升级——Java/Maven + LLM + 区段级只读）/ chg-02（SCRIPTS detector 注册化）
新增 pytest 用例：覆盖 Maven / Gradle / Cargo / .NET / 多语言共存 / PetMallPlatform-like fixture。

TC-01: Maven lifecycle detector（pom.xml + spring-boot-maven-plugin → 4 行 mvn 命令）
TC-02: Gradle lifecycle detector（build.gradle + org.springframework.boot → 3 行 gradlew 命令）
TC-03: Cargo bin detector（Cargo.toml + [[bin]] → 3 行 cargo 命令）
TC-04: DotNet sln detector（*.sln / *.csproj → 3 行 dotnet 命令）
TC-05: baseline Python compat（pyproject.toml [project.scripts] + Makefile → 含 entrypoint + make targets）
TC-06: 多语言 detector 共存（pom.xml + package.json + Makefile → 全部命令）
TC-PetMall: PetMallPlatform-like（root pom.xml + 5 个 platform-* 子目录 → SCRIPTS 命中 Maven 命令）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
sys.path.insert(0, SRC_DIR)

from harness_workflow.tools.harness_playbook_refresh import (
    _scan_scripts,
    MavenLifecycleDetector,
    GradleLifecycleDetector,
    CargoBinDetector,
    DotNetSlnDetector,
    PyProjectScriptsDetector,
    MakefileTargetsDetector,
    PackageJsonScriptsDetector,
    DEFAULT_SCRIPT_DETECTORS,
)
from harness_workflow.playbook.skeleton import render_skeleton, PLAYBOOK_ROOT_SUFFIX
from harness_workflow.tools.harness_playbook_refresh import playbook_refresh


# ---------------------------------------------------------------------------
# TC-01: Maven lifecycle detector
# ---------------------------------------------------------------------------

def test_tc01_maven_scripts_detector(tmp_path):
    """TC-01: pom.xml + spring-boot-maven-plugin → _scan_scripts 输出含 mvn clean install / mvn test / mvn package / mvn spring-boot:run 4 行。"""
    (tmp_path / "pom.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <groupId>com.example</groupId>
  <artifactId>my-service</artifactId>
  <version>1.0.0</version>
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

    result = _scan_scripts(tmp_path)

    assert "mvn clean install" in result, f"缺少 mvn clean install: {result}"
    assert "mvn test" in result, f"缺少 mvn test: {result}"
    assert "mvn package" in result, f"缺少 mvn package: {result}"
    assert "mvn spring-boot:run" in result, f"缺少 mvn spring-boot:run: {result}"
    # 不应含 baseline 占位符
    assert "未检测到脚本配置" not in result


def test_tc01b_maven_without_spring_boot(tmp_path):
    """TC-01b: pom.xml 不含 spring-boot-maven-plugin → 输出 3 行 mvn 命令（无 spring-boot:run）。"""
    (tmp_path / "pom.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <artifactId>plain-java</artifactId>
</project>
""",
        encoding="utf-8",
    )

    result = _scan_scripts(tmp_path)

    assert "mvn clean install" in result
    assert "mvn test" in result
    assert "mvn package" in result
    assert "mvn spring-boot:run" not in result


# ---------------------------------------------------------------------------
# TC-02: Gradle lifecycle detector
# ---------------------------------------------------------------------------

def test_tc02_gradle_scripts_detector(tmp_path):
    """TC-02: build.gradle + org.springframework.boot → _scan_scripts 输出含 ./gradlew build / ./gradlew test / ./gradlew bootRun。"""
    (tmp_path / "build.gradle").write_text(
        """plugins {
    id 'org.springframework.boot' version '3.1.0'
    id 'java'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
}
""",
        encoding="utf-8",
    )

    result = _scan_scripts(tmp_path)

    assert "./gradlew build" in result, f"缺少 ./gradlew build: {result}"
    assert "./gradlew test" in result, f"缺少 ./gradlew test: {result}"
    assert "./gradlew bootRun" in result, f"缺少 ./gradlew bootRun: {result}"


def test_tc02b_gradle_kts_without_spring_boot(tmp_path):
    """TC-02b: build.gradle.kts 不含 org.springframework.boot → 输出 2 行 gradlew 命令（无 bootRun）。"""
    (tmp_path / "build.gradle.kts").write_text(
        """plugins {
    kotlin("jvm") version "1.9.0"
}
""",
        encoding="utf-8",
    )

    result = _scan_scripts(tmp_path)

    assert "./gradlew build" in result
    assert "./gradlew test" in result
    assert "./gradlew bootRun" not in result


# ---------------------------------------------------------------------------
# TC-03: Cargo bin detector
# ---------------------------------------------------------------------------

def test_tc03_cargo_bin_detector(tmp_path):
    """TC-03: Cargo.toml + [[bin]] → _scan_scripts 输出含 cargo build / cargo test / cargo run。"""
    (tmp_path / "Cargo.toml").write_text(
        """[package]
name = "my-tool"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "my-tool"
path = "src/main.rs"
""",
        encoding="utf-8",
    )

    result = _scan_scripts(tmp_path)

    assert "cargo build" in result, f"缺少 cargo build: {result}"
    assert "cargo test" in result, f"缺少 cargo test: {result}"
    assert "cargo run" in result, f"缺少 cargo run: {result}"


def test_tc03b_cargo_without_bin(tmp_path):
    """TC-03b: Cargo.toml 不含 [[bin]] → 输出 2 行 cargo 命令（无 cargo run）。"""
    (tmp_path / "Cargo.toml").write_text(
        """[package]
name = "my-lib"
version = "0.1.0"
edition = "2021"

[lib]
name = "my_lib"
""",
        encoding="utf-8",
    )

    result = _scan_scripts(tmp_path)

    assert "cargo build" in result
    assert "cargo test" in result
    assert "cargo run" not in result


# ---------------------------------------------------------------------------
# TC-04: DotNet sln / csproj detector
# ---------------------------------------------------------------------------

def test_tc04_dotnet_sln_detector(tmp_path):
    """TC-04: *.sln 存在 → _scan_scripts 输出含 dotnet build / dotnet test / dotnet run。"""
    (tmp_path / "Solution.sln").write_text(
        "Microsoft Visual Studio Solution File, Format Version 12.00\n",
        encoding="utf-8",
    )

    result = _scan_scripts(tmp_path)

    assert "dotnet build" in result, f"缺少 dotnet build: {result}"
    assert "dotnet test" in result, f"缺少 dotnet test: {result}"
    assert "dotnet run" in result, f"缺少 dotnet run: {result}"


def test_tc04b_dotnet_csproj_detector(tmp_path):
    """TC-04b: *.csproj 存在（无 .sln） → 同样输出 dotnet 命令。"""
    (tmp_path / "Project.csproj").write_text(
        """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
""",
        encoding="utf-8",
    )

    result = _scan_scripts(tmp_path)

    assert "dotnet build" in result
    assert "dotnet test" in result
    assert "dotnet run" in result


# ---------------------------------------------------------------------------
# TC-05: baseline Python compat
# ---------------------------------------------------------------------------

def test_tc05_baseline_python_scripts_compat(tmp_path):
    """TC-05: pyproject.toml [project.scripts] + Makefile → 含 entrypoint + make targets。"""
    (tmp_path / "pyproject.toml").write_text(
        """[project]
name = "myapp"
version = "1.0.0"

[project.scripts]
myapp = "myapp.main:main"
myapp-cli = "myapp.cli:cli_main"
""",
        encoding="utf-8",
    )
    (tmp_path / "Makefile").write_text(
        "test:\n\tpytest tests/ -v\n\nbuild:\n\tpython -m build\n",
        encoding="utf-8",
    )

    result = _scan_scripts(tmp_path)

    # entrypoints
    assert "myapp" in result, f"缺少 myapp entrypoint: {result}"
    assert "myapp.main:main" in result, f"缺少 target: {result}"
    # make targets
    assert "make test" in result, f"缺少 make test: {result}"
    assert "make build" in result, f"缺少 make build: {result}"
    # 不含占位符
    assert "未检测到脚本配置" not in result


# ---------------------------------------------------------------------------
# TC-06: 多语言 detector 共存
# ---------------------------------------------------------------------------

def test_tc06_multi_build_system_coexistence(tmp_path):
    """TC-06: pom.xml + package.json + Makefile 共存 → 所有构建系统命令全部出现（无相互排斥）。"""
    # Maven
    (tmp_path / "pom.xml").write_text(
        "<project><artifactId>multi-build</artifactId></project>",
        encoding="utf-8",
    )
    # npm
    (tmp_path / "package.json").write_text(
        '{"name":"frontend","scripts":{"dev":"vite","build":"vite build"}}',
        encoding="utf-8",
    )
    # Makefile
    (tmp_path / "Makefile").write_text(
        "deploy:\n\t./deploy.sh\n",
        encoding="utf-8",
    )

    result = _scan_scripts(tmp_path)

    # Maven 命令
    assert "mvn clean install" in result, f"缺少 mvn clean install: {result}"
    # npm 命令
    assert "npm run dev" in result, f"缺少 npm run dev: {result}"
    assert "npm run build" in result, f"缺少 npm run build: {result}"
    # make 命令
    assert "make deploy" in result, f"缺少 make deploy: {result}"


# ---------------------------------------------------------------------------
# TC-PetMall: PetMallPlatform-like fixture
# ---------------------------------------------------------------------------

def test_tc_petmall_platform_like(tmp_path):
    """TC-PetMall: root pom.xml + 5 个 platform-* 子目录 → SCRIPTS 区段命中 Maven 命令。"""
    # root pom.xml（父 pom）
    (tmp_path / "pom.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <groupId>com.petmall</groupId>
  <artifactId>PetMallPlatform</artifactId>
  <version>1.0.0</version>
  <packaging>pom</packaging>
  <modules>
    <module>platform-user</module>
    <module>platform-product</module>
    <module>platform-order</module>
    <module>platform-payment</module>
    <module>platform-gateway</module>
  </modules>
</project>
""",
        encoding="utf-8",
    )

    # 创建 5 个平台子模块目录
    for module in ["platform-user", "platform-product", "platform-order", "platform-payment", "platform-gateway"]:
        module_dir = tmp_path / module
        module_dir.mkdir()
        (module_dir / "pom.xml").write_text(
            f"""<project>
  <parent>
    <groupId>com.petmall</groupId>
    <artifactId>PetMallPlatform</artifactId>
    <version>1.0.0</version>
  </parent>
  <artifactId>{module}</artifactId>
</project>
""",
            encoding="utf-8",
        )
        (module_dir / "src").mkdir()

    result = _scan_scripts(tmp_path)

    # 断言含 Maven 命令（root pom.xml 命中 MavenLifecycleDetector）
    assert "mvn clean install" in result, f"缺少 mvn clean install: {result}"
    assert "mvn test" in result, f"缺少 mvn test: {result}"
    assert "mvn package" in result, f"缺少 mvn package: {result}"
    assert "未检测到脚本配置" not in result


# ---------------------------------------------------------------------------
# TC-Integration: AUTO:SCRIPTS 区段在 playbook_refresh 中体现 Maven 命令
# ---------------------------------------------------------------------------

def test_tc_integration_maven_in_runbook(tmp_path):
    """Integration: Maven fixture + playbook_refresh → architecture.md AUTO:SCRIPTS 含 mvn 命令。"""
    render_skeleton(tmp_path, ["core"])

    (tmp_path / "pom.xml").write_text(
        """<project>
  <artifactId>spring-service</artifactId>
  <build>
    <plugins>
      <plugin>
        <artifactId>spring-boot-maven-plugin</artifactId>
      </plugin>
    </plugins>
  </build>
</project>
""",
        encoding="utf-8",
    )

    rc = playbook_refresh(tmp_path)
    assert rc == 0, f"playbook_refresh returned {rc}"

    arch_md = tmp_path / PLAYBOOK_ROOT_SUFFIX / "architecture.md"
    content = arch_md.read_text(encoding="utf-8")

    m = re.search(
        r"<!-- AUTO:SCRIPTS -->(.*?)<!-- /AUTO:SCRIPTS -->",
        content,
        re.DOTALL,
    )
    assert m, "AUTO:SCRIPTS 区段不存在"
    scripts_content = m.group(1)
    assert "mvn clean install" in scripts_content, f"AUTO:SCRIPTS 未含 mvn clean install: {scripts_content}"
    assert "mvn spring-boot:run" in scripts_content, f"AUTO:SCRIPTS 未含 mvn spring-boot:run: {scripts_content}"


# ---------------------------------------------------------------------------
# 单元：detector 类本身的行为
# ---------------------------------------------------------------------------

def test_maven_detector_applies(tmp_path):
    """MavenLifecycleDetector.applies 仅在 pom.xml 存在时为 True。"""
    d = MavenLifecycleDetector()
    assert not d.applies(tmp_path)
    (tmp_path / "pom.xml").write_text("<project/>", encoding="utf-8")
    assert d.applies(tmp_path)


def test_gradle_detector_applies_gradlew(tmp_path):
    """GradleLifecycleDetector.applies 在 gradlew 存在时为 True（无 build.gradle）。"""
    d = GradleLifecycleDetector()
    assert not d.applies(tmp_path)
    (tmp_path / "gradlew").write_text("#!/bin/sh\n", encoding="utf-8")
    assert d.applies(tmp_path)


def test_dotnet_detector_applies_csproj(tmp_path):
    """DotNetSlnDetector.applies 在 *.csproj 存在时为 True。"""
    d = DotNetSlnDetector()
    assert not d.applies(tmp_path)
    (tmp_path / "App.csproj").write_text("<Project/>", encoding="utf-8")
    assert d.applies(tmp_path)


def test_default_script_detectors_count():
    """DEFAULT_SCRIPT_DETECTORS 包含 7 个 detector（baseline 3 + 新增 4）。"""
    assert len(DEFAULT_SCRIPT_DETECTORS) == 7


def test_no_match_returns_placeholder(tmp_path):
    """空目录 → _scan_scripts 返回 baseline 占位符。"""
    result = _scan_scripts(tmp_path)
    assert "未检测到脚本配置" in result
