"""tests/test_domain_inference_multi_lang.py

req-56（路书引擎升级-java-maven-多模块-llm-内容填充-区段级只读）/ chg-01（推断器多语言注册化）
多语言 detector 注册器架构测试套件

TC-01: PetMallPlatform-like Maven multi-module（root pom.xml <modules>）
TC-02: Maven 兜底（无 root <modules> 但子目录有 pom.xml）
TC-03: Gradle multi-module（settings.gradle include 列表）
TC-04: Gradle Kotlin DSL（settings.gradle.kts include(...)）
TC-05: Cargo workspace（Cargo.toml [workspace] members 显式列表）
TC-06: Cargo workspace glob（members = ["crates/*"]）
TC-07: .NET sln（*.sln Project 行）
TC-08: override_domains 跳过推断器
TC-09: baseline Python 4 级降级兼容（src/modules/*）
TC-10: baseline Python 4 级降级兼容（src/domains/*）
TC-11: baseline Python 4 级降级兼容（app/*）
TC-12: baseline Python 4 级降级兼容（src/{pkg}/* 次级模块）
TC-13: PetMallPlatform 5 模块完整 fixture
TC-14: Maven 优先于 Python（Maven pom + src/modules 同存在）
TC-15: detector 注入（自定义 detectors 参数）
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
sys.path.insert(0, SRC_DIR)

from harness_workflow.playbook.domain_inference import (
    infer_domains,
    MavenMultiModuleDetector,
    GradleMultiModuleDetector,
    CargoWorkspaceDetector,
    DotNetSlnDetector,
    PythonModulesDetector,
)


# ---------------------------------------------------------------------------
# TC-01: PetMallPlatform-like Maven multi-module（root pom.xml <modules>）
# ---------------------------------------------------------------------------

def test_tc01_maven_root_pom_modules(tmp_path, capsys):
    """TC-01: root pom.xml 含 <modules>，提取 5 模块名。"""
    root_pom = tmp_path / "pom.xml"
    root_pom.write_text(
        '<?xml version="1.0"?>\n'
        '<project>\n'
        '  <modules>\n'
        '    <module>platform-admin</module>\n'
        '    <module>platform-common</module>\n'
        '    <module>platform-modules</module>\n'
        '    <module>platform-extend</module>\n'
        '    <module>platform-demo-ui</module>\n'
        '  </modules>\n'
        '</project>\n',
        encoding="utf-8",
    )
    # 创建模块目录 + 噪声目录
    for mod in ["platform-admin", "platform-common", "platform-modules",
                "platform-extend", "platform-demo-ui"]:
        (tmp_path / mod / "src" / "main" / "java").mkdir(parents=True)
    (tmp_path / "app" / "logs").mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "maven_multi_module"
    assert set(domains) == {
        "platform-admin", "platform-common", "platform-modules",
        "platform-extend", "platform-demo-ui",
    }
    # logs 噪声目录不应出现
    assert "logs" not in domains
    assert "matched 'maven_multi_module'" in captured.out


# ---------------------------------------------------------------------------
# TC-02: Maven 兜底（无 root <modules> 但子目录有 pom.xml）
# ---------------------------------------------------------------------------

def test_tc02_maven_fallback_subdirs_with_pom(tmp_path, capsys):
    """TC-02: root pom.xml 无 <modules> 但 >=2 个子目录有 pom.xml，命中 fallback。"""
    root_pom = tmp_path / "pom.xml"
    root_pom.write_text(
        '<?xml version="1.0"?>\n<project><artifactId>parent</artifactId></project>\n',
        encoding="utf-8",
    )
    for mod in ["platform-admin", "platform-common"]:
        (tmp_path / mod).mkdir()
        (tmp_path / mod / "pom.xml").write_text(
            f'<project><artifactId>{mod}</artifactId></project>\n',
            encoding="utf-8",
        )

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "maven_multi_module"
    assert set(domains) == {"platform-admin", "platform-common"}
    assert "matched 'maven_multi_module'" in captured.out


# ---------------------------------------------------------------------------
# TC-03: Gradle multi-module（settings.gradle）
# ---------------------------------------------------------------------------

def test_tc03_gradle_settings_include(tmp_path, capsys):
    """TC-03: settings.gradle 含 include 'mod-a', 'mod-b'。"""
    settings = tmp_path / "settings.gradle"
    settings.write_text(
        "rootProject.name = 'my-project'\n"
        "include 'mod-a', 'mod-b'\n",
        encoding="utf-8",
    )
    (tmp_path / "mod-a").mkdir()
    (tmp_path / "mod-b").mkdir()

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "gradle_multi_module"
    assert "mod-a" in domains
    assert "mod-b" in domains
    assert "matched 'gradle_multi_module'" in captured.out


# ---------------------------------------------------------------------------
# TC-04: Gradle Kotlin DSL（settings.gradle.kts）
# ---------------------------------------------------------------------------

def test_tc04_gradle_kts_include(tmp_path, capsys):
    """TC-04: settings.gradle.kts 含 include('app'), include('lib')。"""
    settings = tmp_path / "settings.gradle.kts"
    settings.write_text(
        'rootProject.name = "my-app"\n'
        'include("app")\n'
        'include("lib")\n',
        encoding="utf-8",
    )

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "gradle_multi_module"
    assert "app" in domains
    assert "lib" in domains
    assert "matched 'gradle_multi_module'" in captured.out


# ---------------------------------------------------------------------------
# TC-05: Cargo workspace（显式 members 列表）
# ---------------------------------------------------------------------------

def test_tc05_cargo_workspace_explicit_members(tmp_path, capsys):
    """TC-05: Cargo.toml [workspace] members = ["core", "cli"]。"""
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text(
        '[workspace]\nmembers = [\n  "core",\n  "cli",\n]\n',
        encoding="utf-8",
    )

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "cargo_workspace"
    assert set(domains) == {"core", "cli"}
    assert "matched 'cargo_workspace'" in captured.out


# ---------------------------------------------------------------------------
# TC-06: Cargo workspace glob（members = ["crates/*"]）
# ---------------------------------------------------------------------------

def test_tc06_cargo_workspace_glob_members(tmp_path, capsys):
    """TC-06: Cargo.toml [workspace] members glob crates/* 展开。"""
    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text(
        '[workspace]\nmembers = ["crates/*"]\n',
        encoding="utf-8",
    )
    for crate in ["foo", "bar", "baz"]:
        (tmp_path / "crates" / crate).mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "cargo_workspace"
    assert set(domains) == {"foo", "bar", "baz"}
    assert "matched 'cargo_workspace'" in captured.out


# ---------------------------------------------------------------------------
# TC-07: .NET sln
# ---------------------------------------------------------------------------

def test_tc07_dotnet_sln(tmp_path, capsys):
    """TC-07: Solution.sln 含 2 Project 行。"""
    sln = tmp_path / "Solution.sln"
    sln.write_text(
        'Microsoft Visual Studio Solution File\n'
        'Project("{FAE04EC0}") = "WebApi", "WebApi/WebApi.csproj", "{GUID1}"\n'
        'EndProject\n'
        'Project("{FAE04EC0}") = "DataLayer", "DataLayer/DataLayer.csproj", "{GUID2}"\n'
        'EndProject\n',
        encoding="utf-8",
    )
    # 创建对应顶层目录
    (tmp_path / "WebApi").mkdir()
    (tmp_path / "DataLayer").mkdir()

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "dotnet_sln"
    assert "WebApi" in domains
    assert "DataLayer" in domains
    assert "matched 'dotnet_sln'" in captured.out


# ---------------------------------------------------------------------------
# TC-08: override_domains 跳过推断器
# ---------------------------------------------------------------------------

def test_tc08_override_domains(tmp_path, capsys):
    """TC-08: override_domains=['custom-a', 'custom-b'] 直接用，不走推断器。"""
    # 不建任何 detector 可命中的结构
    mode, domains = infer_domains(tmp_path, override_domains=["custom-a", "custom-b"])

    captured = capsys.readouterr()
    assert mode == "user-specified (--domains)"
    assert domains == ["custom-a", "custom-b"]
    assert "user-provided" in captured.out
    assert "custom-a" in captured.out
    assert "custom-b" in captured.out


# ---------------------------------------------------------------------------
# TC-09～TC-12: baseline Python 4 级降级兼容（req-55 TC-01～TC-04 同 fixture）
# ---------------------------------------------------------------------------

def test_tc09_baseline_level1_modules(tmp_path, capsys):
    """TC-09: baseline Level-1 src/modules/* 兼容（mode 字面量不变）。"""
    (tmp_path / "src" / "modules" / "auth").mkdir(parents=True)
    (tmp_path / "src" / "modules" / "order").mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "src/modules/*"
    assert set(domains) == {"auth", "order"}
    assert "matched 'src/modules/*'" in captured.out


def test_tc10_baseline_level2_domains(tmp_path, capsys):
    """TC-10: baseline Level-2 src/domains/* 兼容。"""
    (tmp_path / "src" / "domains" / "user").mkdir(parents=True)
    (tmp_path / "src" / "domains" / "payment").mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "src/domains/*"
    assert set(domains) == {"user", "payment"}


def test_tc11_baseline_level3_app(tmp_path, capsys):
    """TC-11: baseline Level-3 app/* 兼容。"""
    (tmp_path / "app" / "web").mkdir(parents=True)
    (tmp_path / "app" / "worker").mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "app/*"
    assert set(domains) == {"web", "worker"}


def test_tc12_baseline_level4_single_pkg(tmp_path, capsys):
    """TC-12: baseline Level-4 src/{pkg}/*次级模块 兼容。"""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "mypkg"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "src" / "mypkg" / "bar").mkdir(parents=True)
    (tmp_path / "src" / "mypkg" / "baz").mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    # mode 返回字面量 'src/{pkg}/*次级模块'（与 req-55 baseline 兼容），打印时展开
    assert mode == "src/{pkg}/*次级模块"
    assert set(domains) == {"bar", "baz"}
    assert "matched 'src/mypkg/*次级模块'" in captured.out


# ---------------------------------------------------------------------------
# TC-13: PetMallPlatform 5 模块完整 fixture
# ---------------------------------------------------------------------------

def test_tc13_petmall_platform_like_fixture(tmp_path, capsys):
    """TC-13: PetMallPlatform 完整结构 5 个 platform-* 模块 + root pom.xml。"""
    modules = [
        "platform-admin",
        "platform-common",
        "platform-modules",
        "platform-extend",
        "platform-demo-ui",
    ]
    # root pom.xml with <modules>
    root_pom_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<project>\n'
        '  <groupId>com.pet</groupId>\n'
        '  <artifactId>petmall</artifactId>\n'
        '  <packaging>pom</packaging>\n'
        '  <modules>\n'
    )
    for mod in modules:
        root_pom_content += f'    <module>{mod}</module>\n'
    root_pom_content += '  </modules>\n</project>\n'
    (tmp_path / "pom.xml").write_text(root_pom_content, encoding="utf-8")

    # 每个模块含 pom.xml + src/main/java/
    for mod in modules:
        mod_dir = tmp_path / mod
        (mod_dir / "src" / "main" / "java").mkdir(parents=True)
        (mod_dir / "pom.xml").write_text(
            f'<project><artifactId>{mod}</artifactId></project>\n',
            encoding="utf-8",
        )

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "maven_multi_module"
    assert set(domains) == set(modules)
    assert len(domains) == 5
    assert "matched 'maven_multi_module'" in captured.out
    assert "5 domains" in captured.out


# ---------------------------------------------------------------------------
# TC-14: Maven 优先于 Python（Maven pom 和 src/modules 同时存在）
# ---------------------------------------------------------------------------

def test_tc14_maven_priority_over_python(tmp_path, capsys):
    """TC-14: 同时有 root pom.xml <modules> 和 src/modules/，Maven 优先命中。"""
    root_pom = tmp_path / "pom.xml"
    root_pom.write_text(
        '<project><modules><module>service-a</module><module>service-b</module></modules></project>',
        encoding="utf-8",
    )
    # 也建 Python 结构
    (tmp_path / "src" / "modules" / "auth").mkdir(parents=True)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "maven_multi_module"
    assert set(domains) == {"service-a", "service-b"}


# ---------------------------------------------------------------------------
# TC-15: detector 注入（自定义 detectors 参数）
# ---------------------------------------------------------------------------

def test_tc15_custom_detectors_injection(tmp_path, capsys):
    """TC-15: detectors 参数注入单个 PythonModulesDetector，仅该 detector 生效。"""
    # 建 src/modules/ + 也建 root pom.xml（不应命中，因为注入的是 Python detector）
    (tmp_path / "src" / "modules" / "alpha").mkdir(parents=True)
    (tmp_path / "pom.xml").write_text(
        '<project><modules><module>svc</module></modules></project>',
        encoding="utf-8",
    )

    mode, domains = infer_domains(tmp_path, detectors=[PythonModulesDetector()])

    captured = capsys.readouterr()
    assert mode == "src/modules/*"
    assert "alpha" in domains
    # Maven 没被注入，不应命中
    assert "svc" not in domains
