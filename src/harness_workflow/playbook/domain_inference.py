"""领域推断器（req-56（路书引擎升级-java-maven-多模块-llm-内容填充-区段级只读）/ chg-01（推断器多语言注册化））

重构为 detector 注册器架构（OQ-1=B1 决策）：
  - 抽象基类 DomainDetector
  - 8 类 detector（MavenMultiModule / GradleMultiModule / CargoWorkspace / DotNetSln
                    + Python 4 级降级 baseline 兼容：PythonModules / PythonDomains / AppDir / PythonPackage）
  - DEFAULT_DETECTORS 注册列表，按 priority 升序遍历，命中即停
  - infer_domains(root, override_domains=None, detectors=None) 主入口
  - _print_matched helper（stdout 命中打印）

保留 req-55 baseline 4 级降级语义（Python detector priority=50/60/70/80 排在最后）。
返回 (matched_mode: str, domains: list[str])。
推断器永远软失败（零结果 return ('no-match', []) + stderr WARN，不 abort）。
"""
from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_pkg_name(root: Path) -> Optional[str]:
    """从 pyproject.toml / setup.py / src/ 唯一子目录名推断单包包名。"""
    # 1) pyproject.toml [project] name 或 [tool.poetry] name
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
            # [project] name = "..."
            m = re.search(r'^\[project\]\s*\n(?:.*\n)*?name\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
            if m:
                return m.group(1).replace("-", "_")
            # [tool.poetry] name = "..."
            m = re.search(r'^\[tool\.poetry\]\s*\n(?:.*\n)*?name\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
            if m:
                return m.group(1).replace("-", "_")
        except Exception:
            pass

    # 2) setup.py name= (简单 grep)
    setup_py = root / "setup.py"
    if setup_py.exists():
        try:
            content = setup_py.read_text(encoding="utf-8")
            m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if m:
                return m.group(1).replace("-", "_")
        except Exception:
            pass

    # 3) src/ 下唯一非 __pycache__ 子目录名
    src_dir = root / "src"
    if src_dir.is_dir():
        subdirs = [
            d.name for d in src_dir.iterdir()
            if d.is_dir() and d.name != "__pycache__" and not d.name.startswith(".")
        ]
        if len(subdirs) == 1:
            return subdirs[0]

    return None


def _list_subdirs(parent: Path) -> list[str]:
    """列出 parent 下所有非 __pycache__ 非隐藏子目录名，排序。"""
    if not parent.is_dir():
        return []
    return sorted(
        d.name for d in parent.iterdir()
        if d.is_dir() and d.name != "__pycache__" and not d.name.startswith(".")
    )


def _print_matched(mode: str, domains: list[str], pkg: Optional[str] = None) -> None:
    """stdout 打印命中级别（让用户感知命中哪类 detector）。"""
    count = len(domains)
    domain_str = ", ".join(domains)
    if pkg and "{pkg}" in mode:
        display_mode = mode.replace("{pkg}", pkg)
    else:
        display_mode = mode
    print(f"domain inference: matched '{display_mode}' ({count} domains: {domain_str})")


# ---------------------------------------------------------------------------
# 抽象基类
# ---------------------------------------------------------------------------

class DomainDetector(ABC):
    """detector 注册器基类。priority 数字越小越优先（按 priority 升序遍历，命中即停）。"""

    name: str   # 命中 stdout 打印用
    priority: int  # 0=最优先

    @abstractmethod
    def detect(self, root: Path) -> Optional[tuple[str, list[str]]]:
        """命中返回 (matched_mode, domains)，未命中返回 None。"""


# ---------------------------------------------------------------------------
# 多语言 detector（priority=10~40）
# ---------------------------------------------------------------------------

class MavenMultiModuleDetector(DomainDetector):
    """priority=10，name='maven_multi_module'

    扫 {root}/pom.xml 中 <modules> 段提取子模块名。
    若无 <modules> 但根下有 >=2 个含 pom.xml 的子目录 → A3 fallback。
    """
    name = "maven_multi_module"
    priority = 10

    def detect(self, root: Path) -> Optional[tuple[str, list[str]]]:
        pom = root / "pom.xml"
        if not pom.exists():
            return None

        content = pom.read_text(encoding="utf-8", errors="replace")

        # 尝试从 <modules>...</modules> 提取
        modules_block = re.search(r'<modules>(.*?)</modules>', content, re.DOTALL)
        if modules_block:
            module_names = re.findall(r'<module>\s*([^<\s]+)\s*</module>', modules_block.group(1))
            if module_names:
                return self.name, module_names

        # A3 fallback：根下 >=2 个含 pom.xml 的子目录
        subdirs_with_pom = sorted(
            d.name for d in root.iterdir()
            if d.is_dir() and not d.name.startswith(".")
            and (d / "pom.xml").exists()
        )
        if len(subdirs_with_pom) >= 2:
            return self.name, subdirs_with_pom

        return None


class GradleMultiModuleDetector(DomainDetector):
    """priority=20，name='gradle_multi_module'

    扫 {root}/settings.gradle 或 settings.gradle.kts，提取 include 列表。
    支持 include 'mod-a', 'mod-b' 和 include("mod-a") 两种风格。
    """
    name = "gradle_multi_module"
    priority = 20

    def detect(self, root: Path) -> Optional[tuple[str, list[str]]]:
        for filename in ("settings.gradle", "settings.gradle.kts"):
            settings = root / filename
            if not settings.exists():
                continue
            content = settings.read_text(encoding="utf-8", errors="replace")
            # 提取所有含 include 的行/表达式（包括 include 'a', 'b' 和 include("a")）
            # 步骤1：找所有 include 语句（直到行尾或分号）
            include_stmts = re.findall(r'include\s*[^\n;]+', content)
            names = []
            for stmt in include_stmts:
                # 从每个 include 语句中提取所有单/双引号内容
                found = re.findall(r"""['"]([^'"]+)['"]""", stmt)
                names.extend(found)
            if names:
                return self.name, sorted(set(names))
        return None


class CargoWorkspaceDetector(DomainDetector):
    """priority=30，name='cargo_workspace'

    扫 {root}/Cargo.toml [workspace] members = [...] 字段。
    支持显式名（crates/foo）和 glob（crates/*）。
    """
    name = "cargo_workspace"
    priority = 30

    def detect(self, root: Path) -> Optional[tuple[str, list[str]]]:
        cargo_toml = root / "Cargo.toml"
        if not cargo_toml.exists():
            return None
        content = cargo_toml.read_text(encoding="utf-8", errors="replace")

        # 检查是否有 [workspace]
        if not re.search(r'^\[workspace\]', content, re.MULTILINE):
            return None

        # 提取 members = [ ... ] 段
        m = re.search(r'members\s*=\s*\[([^\]]*)\]', content, re.DOTALL)
        if not m:
            return None

        raw_members = re.findall(r'["\']([^"\']+)["\']', m.group(1))
        if not raw_members:
            return None

        domains = []
        for member in raw_members:
            if "*" in member:
                # glob 展开：crates/* → crates/ 下所有目录
                glob_dir = root / member.replace("/*", "").replace("*", "")
                if glob_dir.is_dir():
                    for sub in sorted(glob_dir.iterdir()):
                        if sub.is_dir() and not sub.name.startswith("."):
                            domains.append(sub.name)
            else:
                # 显式路径：取最后一段作领域名
                domains.append(Path(member).name)

        if domains:
            return self.name, sorted(set(domains))
        return None


class DotNetSlnDetector(DomainDetector):
    """priority=40，name='dotnet_sln'

    扫 {root}/*.sln，提取 Project(...) = "ProjectName", "..." 行。
    """
    name = "dotnet_sln"
    priority = 40

    def detect(self, root: Path) -> Optional[tuple[str, list[str]]]:
        sln_files = list(root.glob("*.sln"))
        if not sln_files:
            return None

        domains = []
        for sln in sln_files:
            content = sln.read_text(encoding="utf-8", errors="replace")
            # Project("{GUID}") = "ProjectName", "ProjectName/ProjectName.csproj", "{GUID}"
            names = re.findall(r'^Project\([^)]+\)\s*=\s*"([^"]+)"', content, re.MULTILINE)
            for name in names:
                # 跳过解决方案文件夹（通常 = "Solution Items" 等，无对应目录）
                if (root / name).is_dir():
                    domains.append(name)
                else:
                    # 也收录有对应 csproj 文件的（目录可能不存在但项目有效）
                    domains.append(name)

        if domains:
            return self.name, sorted(set(domains))
        return None


# ---------------------------------------------------------------------------
# Python detector（priority=50~80，保留 req-55 baseline 4 级降级语义）
# ---------------------------------------------------------------------------

class PythonModulesDetector(DomainDetector):
    """priority=50，name='src/modules/*'（req-55 Level-1 baseline）"""
    name = "src/modules/*"
    priority = 50

    def detect(self, root: Path) -> Optional[tuple[str, list[str]]]:
        domains = _list_subdirs(root / "src" / "modules")
        if domains:
            return self.name, domains
        return None


class PythonDomainsDetector(DomainDetector):
    """priority=60，name='src/domains/*'（req-55 Level-2 baseline）"""
    name = "src/domains/*"
    priority = 60

    def detect(self, root: Path) -> Optional[tuple[str, list[str]]]:
        domains = _list_subdirs(root / "src" / "domains")
        if domains:
            return self.name, domains
        return None


class AppDirDetector(DomainDetector):
    """priority=70，name='app/*'（req-55 Level-3 baseline）"""
    name = "app/*"
    priority = 70

    def detect(self, root: Path) -> Optional[tuple[str, list[str]]]:
        domains = _list_subdirs(root / "app")
        if domains:
            return self.name, domains
        return None


class PythonPackageFallbackDetector(DomainDetector):
    """priority=80，name='src/{pkg}/*次级模块'（req-55 Level-4 baseline，单包兜底）

    返回 mode 字面量 'src/{pkg}/*次级模块'（保持 req-55 baseline 兼容），
    打印时由 _print_matched 展开 {pkg} 为实际包名。
    """
    name = "src/{pkg}/*次级模块"
    priority = 80
    _matched_pkg: Optional[str] = None

    def detect(self, root: Path) -> Optional[tuple[str, list[str]]]:
        pkg_name = _read_pkg_name(root)
        if pkg_name:
            pkg_dir = root / "src" / pkg_name
            domains = _list_subdirs(pkg_dir)
            if domains:
                self._matched_pkg = pkg_name
                return "src/{pkg}/*次级模块", domains

        # 兜底：所有 src/ 次级目录
        src_dir = root / "src"
        if src_dir.is_dir():
            all_pkgs = sorted(
                d.name for d in src_dir.iterdir()
                if d.is_dir() and d.name != "__pycache__" and not d.name.startswith(".")
            )
            for pkg in all_pkgs:
                domains = _list_subdirs(src_dir / pkg)
                if domains:
                    self._matched_pkg = pkg
                    return "src/{pkg}/*次级模块", domains

        return None


# ---------------------------------------------------------------------------
# 默认注册列表（按 priority 升序）
# ---------------------------------------------------------------------------

DEFAULT_DETECTORS: list[DomainDetector] = [
    MavenMultiModuleDetector(),
    GradleMultiModuleDetector(),
    CargoWorkspaceDetector(),
    DotNetSlnDetector(),
    PythonModulesDetector(),
    PythonDomainsDetector(),
    AppDirDetector(),
    PythonPackageFallbackDetector(),
]


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def infer_domains(
    root: Path,
    override_domains: Optional[list[str]] = None,
    detectors: Optional[list[DomainDetector]] = None,
) -> tuple[str, list[str]]:
    """推断项目领域结构，返回 (matched_mode, domains)。

    Args:
        root: 仓库根目录。
        override_domains: 非 None 时直接用，不走推断器（--domains flag 逃生口）。
        detectors: 自定义 detector 列表（测试注入 / 功能扩展），默认 DEFAULT_DETECTORS。

    Returns:
        (matched_mode, domains)。软失败：全部未命中时返回 ('no-match', []) + stderr WARN。

    stdout 打印形如:
        domain inference: matched 'maven_multi_module' (5 domains: platform-admin, ...)
    """
    root = Path(root).resolve()

    # override_domains 直接用（--domains flag 逃生口）
    if override_domains is not None:
        mode = "user-specified (--domains)"
        count = len(override_domains)
        domain_str = ", ".join(override_domains)
        print(f"domain inference: user-provided ({count} domains: {domain_str})")
        return mode, list(override_domains)

    # 注册器遍历
    active_detectors = sorted(
        detectors if detectors is not None else DEFAULT_DETECTORS,
        key=lambda d: d.priority,
    )

    for detector in active_detectors:
        result = detector.detect(root)
        if result is not None:
            matched_mode, domains = result
            # PythonPackageFallbackDetector 的 {pkg} 展开：从 detector 实例获取真实包名
            pkg_hint = getattr(detector, "_matched_pkg", None)
            _print_matched(matched_mode, domains, pkg=pkg_hint)
            return matched_mode, domains

    # 零命中软失败
    print(
        "[domain inference] WARN: 无法推断出任何领域，请手工配置 artifacts/project/playbooks/domains/",
        file=sys.stderr,
    )
    return "no-match", []
