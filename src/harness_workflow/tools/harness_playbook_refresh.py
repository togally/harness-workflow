"""harness playbook-refresh 子命令（req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-04（harness playbook-refresh 子命令））

刷新 artifacts/project/playbooks/ 内 5 类 <!-- AUTO:* --> 自动区段：
  - AUTO:STACK       → architecture.md（扫 pyproject.toml / package.json 等）
  - AUTO:SCRIPTS     → architecture.md（扫 Makefile / package.json scripts）
  - AUTO:LAYOUT      → architecture.md（顶层目录树，深度 2，过滤噪声目录）
  - AUTO:DOMAIN_FILES→ code-map.md 与各 domains/*/code.md
  - AUTO:DOMAIN_LIST → overview.md（扫 domains/ 子目录）

核心规约（chg-01 §5 C-01）：仅替换 <!-- AUTO:X -->…<!-- /AUTO:X --> 区段，
区段标记行本身及区段外所有字节保持 byte-identical；标记缺失则 warn + 跳过。
配对校验（chg-01 §5 C-04）：开标记与闭标记必须同时存在，否则 warn + abort 该区段。
不调 LLM（纯静态分析，spec §四实现要点明示）。
"""
from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path


# ---------------------------------------------------------------------------
# 路径锁定（OQ-1=B）
# ---------------------------------------------------------------------------

PLAYBOOK_ROOT_SUFFIX = "artifacts/project/playbooks"

# 目录扫描时过滤的噪声目录名
_NOISE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".mypy_cache", ".pytest_cache", ".tox", "dist", "build",
    ".eggs", "*.egg-info",
}

# 构建产物目录 IGNORE 列表（chg-C Step 4.2：忽略构建产物，防止污染路书）
IGNORE_DIRS: set[str] = {
    "target", "build", "dist", "node_modules", "__pycache__",
    ".git", ".gradle", ".idea", ".vscode", ".pytest_cache",
    "out", "bin", "obj", ".tox", ".venv", "venv",
    "logs",  # 运行时日志
    ".mypy_cache", ".eggs", ".ruff_cache",
}


# ---------------------------------------------------------------------------
# 核心 helper：AUTO 区段替换
# ---------------------------------------------------------------------------

def replace_auto_section(
    content: str,
    marker: str,
    new_content: str,
    prefix: str = "AUTO",
) -> tuple[str, bool, str]:
    """替换文本中的 {prefix}:marker 区段内容。

    规则：
    1. 开/闭标记必须配对（C-04），不配对则返回 (content, False, warn_msg)。
    2. 仅替换区段内容（含包围标记行），区段外 byte-identical（C-01）。
    3. 替换时保留标记行原貌，只换标记之间的内容。

    prefix 参数：默认 "AUTO"（保持 chg-01/02/03 向后兼容），传入 "LLM" 时处理 LLM 区段。

    返回 (new_content, success, warn_msg)。
    """
    open_tag = f"<!-- {prefix}:{marker} -->"
    close_tag = f"<!-- /{prefix}:{marker} -->"

    open_present = open_tag in content
    close_present = close_tag in content

    if not open_present and not close_present:
        return content, False, f"[playbook-refresh] WARN: 标记缺失 {open_tag} 和 {close_tag}，跳过"
    if not open_present:
        return content, False, f"[playbook-refresh] WARN: 缺少开标记 {open_tag}（C-04 配对校验失败），跳过"
    if not close_present:
        return content, False, f"[playbook-refresh] WARN: 缺少闭标记 {close_tag}（C-04 配对校验失败），跳过"

    # 用正则替换区段（含包围标记行）
    pattern = re.compile(
        re.escape(open_tag) + r".*?" + re.escape(close_tag),
        re.DOTALL,
    )

    # 构建替换块：开标记 + \n + 新内容 + \n + 闭标记
    new_block = open_tag + "\n" + new_content.rstrip("\n") + "\n" + close_tag

    result, n = pattern.subn(new_block, content, count=1)
    if n == 0:
        return content, False, f"[playbook-refresh] WARN: 区段替换失败（正则无命中）{open_tag}"

    return result, True, ""


# ---------------------------------------------------------------------------
# 扫描函数：5 类 AUTO 区段内容
# ---------------------------------------------------------------------------

def _scan_stack(root: Path) -> str:
    """扫描 pyproject.toml / package.json / go.mod / pom.xml / Cargo.toml 提取技术栈。"""
    lines = []

    # Python: pyproject.toml
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="replace")
        # 语言版本
        m = re.search(r'python\s*=\s*["\']([^"\']+)["\']', content)
        if m:
            lines.append(f"- Python: {m.group(1)}")
        else:
            lines.append("- Python (pyproject.toml)")
        # 主要依赖（[tool.poetry.dependencies] 或 [project] dependencies）
        deps_m = re.findall(r'^([a-zA-Z0-9_\-]+)\s*=\s*["\'^~>=!]', content, re.MULTILINE)
        if deps_m:
            # 过滤 python 本身和常见非包名
            filtered = [d for d in deps_m[:10] if d.lower() not in ("python", "name", "version")]
            if filtered:
                lines.append(f"  主要依赖: {', '.join(filtered[:8])}")

    # Node.js: package.json
    package_json = root / "package.json"
    if package_json.exists():
        try:
            import json
            data = json.loads(package_json.read_text(encoding="utf-8"))
            name = data.get("name", "node-project")
            version = data.get("version", "")
            lines.append(f"- Node.js: {name}" + (f" {version}" if version else ""))
            deps = list((data.get("dependencies") or {}).keys())[:5]
            if deps:
                lines.append(f"  主要依赖: {', '.join(deps)}")
        except Exception:
            lines.append("- Node.js (package.json)")

    # Go: go.mod
    go_mod = root / "go.mod"
    if go_mod.exists():
        content = go_mod.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'^go\s+([\d.]+)', content, re.MULTILINE)
        version = m.group(1) if m else ""
        mod_m = re.search(r'^module\s+(\S+)', content, re.MULTILINE)
        mod_name = mod_m.group(1) if mod_m else "go-project"
        lines.append(f"- Go {version}: {mod_name}")

    # Java: pom.xml
    pom = root / "pom.xml"
    if pom.exists():
        content = pom.read_text(encoding="utf-8", errors="replace")
        art_m = re.search(r'<artifactId>([^<]+)</artifactId>', content)
        lines.append(f"- Java/Maven: {art_m.group(1) if art_m else 'project'}")

    # Rust: Cargo.toml
    cargo = root / "Cargo.toml"
    if cargo.exists():
        content = cargo.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'^name\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        lines.append(f"- Rust: {m.group(1) if m else 'project'}")

    if not lines:
        lines.append("<!-- 未检测到已知项目文件，请手工填写技术栈 -->")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# SCRIPTS detector 注册化架构（chg-02）
# ---------------------------------------------------------------------------

class ScriptDetector(ABC):
    """SCRIPTS 注册化基类（chg-02，与 chg-01 DomainDetector 同源风格）。

    每个 detector 负责一种构建系统 / 脚本格式的命令检测。
    """
    name: str   # 报告用名称，如 "Maven (mvn lifecycle)"
    priority: int

    @abstractmethod
    def applies(self, root: Path) -> bool:
        """判断此 detector 是否适用于给定项目根目录。"""

    @abstractmethod
    def detect(self, root: Path) -> list[str]:
        """返回命令行列表（格式 "- `cmd`: 注释" 或 "- `cmd`"），未命中返回 []。"""


class PyProjectScriptsDetector(ScriptDetector):
    """扫描 pyproject.toml [project.scripts] / [tool.poetry.scripts] 入口。"""

    name = "PyProject (entrypoints)"
    priority = 10

    def applies(self, root: Path) -> bool:
        return (root / "pyproject.toml").exists()

    def detect(self, root: Path) -> list[str]:
        content = (root / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
        scripts_m = re.findall(r'^(\w[\w\-]+)\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        lines = []
        for name, target in scripts_m[:8]:
            if ":" in target or "." in target:  # 看起来是 entrypoint
                lines.append(f"- `{name}`: {target}")
        return lines


class PackageJsonScriptsDetector(ScriptDetector):
    """扫描 package.json scripts 字段。"""

    name = "npm (package.json scripts)"
    priority = 20

    def applies(self, root: Path) -> bool:
        return (root / "package.json").exists()

    def detect(self, root: Path) -> list[str]:
        try:
            import json
            data = json.loads((root / "package.json").read_text(encoding="utf-8"))
            scripts = data.get("scripts") or {}
            return [f"- `npm run {name}`: {cmd}" for name, cmd in list(scripts.items())[:8]]
        except Exception:
            return []


class MakefileTargetsDetector(ScriptDetector):
    """扫描 Makefile targets。"""

    name = "Makefile targets"
    priority = 30

    def applies(self, root: Path) -> bool:
        return (root / "Makefile").exists()

    def detect(self, root: Path) -> list[str]:
        content = (root / "Makefile").read_text(encoding="utf-8", errors="replace")
        targets = re.findall(r'^([a-zA-Z][a-zA-Z0-9_\-]*)\s*:', content, re.MULTILINE)
        visible = [t for t in targets if not t.startswith(".") and t not in ("PHONY",)]
        return [f"- `make {t}`" for t in visible[:8]]


class MavenLifecycleDetector(ScriptDetector):
    """扫描 pom.xml，存在则输出 Maven lifecycle 标准命令。

    条件附加 mvn spring-boot:run（pom.xml 含 spring-boot-maven-plugin 时）。
    """

    name = "Maven (mvn lifecycle)"
    priority = 40

    def applies(self, root: Path) -> bool:
        return (root / "pom.xml").exists()

    def detect(self, root: Path) -> list[str]:
        lines = [
            "- `mvn clean install`: 构建并安装到本地仓库",
            "- `mvn test`: 跑单元测试",
            "- `mvn package`: 打包",
            "- `mvn dependency:tree`: 依赖树",
        ]
        # 条件附加 spring-boot:run
        try:
            pom_content = (root / "pom.xml").read_text(encoding="utf-8", errors="replace")
            if "<artifactId>spring-boot-maven-plugin</artifactId>" in pom_content:
                lines.insert(3, "- `mvn spring-boot:run`: Spring Boot 启动")
        except Exception:
            pass
        return lines


class GradleLifecycleDetector(ScriptDetector):
    """扫描 build.gradle / build.gradle.kts / gradlew，输出 Gradle lifecycle 命令。

    条件附加 ./gradlew bootRun（gradle 文件含 org.springframework.boot 时）。
    """

    name = "Gradle (gradlew lifecycle)"
    priority = 50

    def applies(self, root: Path) -> bool:
        return (
            (root / "build.gradle").exists()
            or (root / "build.gradle.kts").exists()
            or (root / "gradlew").exists()
        )

    def detect(self, root: Path) -> list[str]:
        lines = [
            "- `./gradlew build`: 构建",
            "- `./gradlew test`: 跑测试",
        ]
        # 条件附加 bootRun
        for gradle_file in ["build.gradle", "build.gradle.kts"]:
            gradle_path = root / gradle_file
            if gradle_path.exists():
                try:
                    content = gradle_path.read_text(encoding="utf-8", errors="replace")
                    if "org.springframework.boot" in content:
                        lines.append("- `./gradlew bootRun`: Spring Boot 启动")
                    break
                except Exception:
                    pass
        return lines


class CargoBinDetector(ScriptDetector):
    """扫描 Cargo.toml，存在则输出 Rust cargo 命令。

    条件附加 cargo run（Cargo.toml 含 [[bin]] 段时）。
    """

    name = "Cargo (Rust)"
    priority = 60

    def applies(self, root: Path) -> bool:
        return (root / "Cargo.toml").exists()

    def detect(self, root: Path) -> list[str]:
        lines = [
            "- `cargo build`: 构建",
            "- `cargo test`: 跑测试",
        ]
        # 条件附加 cargo run
        try:
            content = (root / "Cargo.toml").read_text(encoding="utf-8", errors="replace")
            if "[[bin]]" in content:
                lines.append("- `cargo run`: 运行")
        except Exception:
            pass
        return lines


class DotNetSlnDetector(ScriptDetector):
    """扫描 *.sln / *.csproj，存在则输出 dotnet 命令。"""

    name = "DotNet (.sln / .csproj)"
    priority = 70

    def applies(self, root: Path) -> bool:
        return (
            any(root.glob("*.sln"))
            or any(root.glob("*.csproj"))
        )

    def detect(self, root: Path) -> list[str]:
        return [
            "- `dotnet build`: 构建",
            "- `dotnet test`: 跑测试",
            "- `dotnet run`: 运行",
        ]


# 默认注册器列表（priority 升序）
DEFAULT_SCRIPT_DETECTORS: list[ScriptDetector] = [
    PyProjectScriptsDetector(),
    PackageJsonScriptsDetector(),
    MakefileTargetsDetector(),
    MavenLifecycleDetector(),
    GradleLifecycleDetector(),
    CargoBinDetector(),
    DotNetSlnDetector(),
]


def _scan_scripts(root: Path, detectors: list[ScriptDetector] | None = None) -> str:
    """扫描 scripts 配置，注册器架构（chg-02）。

    与 domain inference 不同：不像命中即停，scripts 多个 build system 可并存，
    所有 detector 命中结果全部汇总输出。
    零命中时输出 baseline 兼容占位符。
    """
    detectors = detectors or DEFAULT_SCRIPT_DETECTORS
    all_lines: list[str] = []

    for d in sorted(detectors, key=lambda x: x.priority):
        if d.applies(root):
            result = d.detect(root)
            if result:
                all_lines.extend(result)

    if not all_lines:
        all_lines.append("<!-- 未检测到脚本配置，请手工填写常用命令 -->")

    return "\n".join(all_lines)


def _scan_layout(root: Path) -> str:
    """扫描顶层目录树（深度 2，过滤噪声目录 + 构建产物目录）。"""
    lines = []
    root_resolved = Path(root).resolve()

    def _is_noise(name: str) -> bool:
        if name.startswith(".") and name not in (".github", ".workflow"):
            return True
        if name in _NOISE_DIRS:
            return True
        if name in IGNORE_DIRS:
            return True
        if name.endswith(".egg-info"):
            return True
        return False

    # 顶层条目
    try:
        top_entries = sorted(root_resolved.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return "<!-- 目录扫描失败 -->"

    for entry in top_entries:
        if _is_noise(entry.name):
            continue
        if entry.is_dir():
            lines.append(f"- `{entry.name}/`")
            # 深度 2：列子目录
            try:
                sub_entries = sorted(entry.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
                for sub in sub_entries:
                    if _is_noise(sub.name):
                        continue
                    if sub.is_dir():
                        lines.append(f"  - `{entry.name}/{sub.name}/`")
                    else:
                        lines.append(f"  - `{entry.name}/{sub.name}`")
            except PermissionError:
                pass
        else:
            lines.append(f"- `{entry.name}`")

    if not lines:
        lines.append("<!-- 目录为空 -->")

    return "\n".join(lines)


def _scan_domain_files(domain_dir: Path, root: Path, domain_name: str) -> str:
    """扫描 domains/<领域>/ 对应源码目录，生成文件清单。

    按 chg-03 / chg-A domain_inference 推断的结构，查找：
    - python/js: src/modules/, src/domains/, app/, src/{pkg}/
    - maven 单层: 顶层 {domain_name}/
    - maven nested（chg-A 递归）: 任意 packaging=pom 父目录下的 {domain_name}/
    """
    lines = []
    candidates = [
        root / "src" / "modules" / domain_name,
        root / "src" / "domains" / domain_name,
        root / "app" / domain_name,
        # maven 顶层模块（chg-A 适配）
        root / domain_name,
    ]
    # 检查 src/{pkg}/{domain_name}（单包兜底）
    src_dir = root / "src"
    if src_dir.is_dir():
        for pkg_dir in src_dir.iterdir():
            if pkg_dir.is_dir() and not pkg_dir.name.startswith(".") and pkg_dir.name != "__pycache__":
                candidates.append(pkg_dir / domain_name)
    # maven nested（chg-A 适配）：扫描顶层每个 packaging=pom 父目录下找 {domain_name}/
    for top_dir in root.iterdir():
        if top_dir.is_dir() and not top_dir.name.startswith(".") and (top_dir / "pom.xml").is_file():
            candidates.append(top_dir / domain_name)

    source_dir = None
    for c in candidates:
        if c.is_dir():
            source_dir = c
            break

    if source_dir is None:
        lines.append(f"<!-- 未找到领域 {domain_name} 对应源码目录，请手工填写 -->")
        return "\n".join(lines)

    # 枚举代码文件（.py / .ts / .go / .java / .rs）
    code_exts = {".py", ".ts", ".tsx", ".js", ".go", ".java", ".rs", ".kt"}
    try:
        for f in sorted(source_dir.rglob("*")):
            # 跳过构建产物目录（chg-C Step 4.2）
            if any(part in IGNORE_DIRS for part in f.parts):
                continue
            if f.is_file() and f.suffix in code_exts:
                # 相对于仓库根的路径
                try:
                    rel = f.relative_to(root)
                    lines.append(f"- `{rel}`: <!-- TODO: 一句话职责描述 -->")
                except ValueError:
                    lines.append(f"- `{f}`: <!-- TODO: 一句话职责描述 -->")
    except PermissionError:
        lines.append("<!-- 文件扫描权限不足 -->")

    if not lines:
        lines.append(f"<!-- 领域 {domain_name} 源码目录无代码文件 -->")

    return "\n".join(lines)


def _scan_domain_list(playbook_root: Path) -> str:
    """扫描 domains/ 子目录列表，生成 DOMAIN_LIST 内容。"""
    domains_dir = playbook_root / "domains"
    if not domains_dir.is_dir():
        return "<!-- 暂无领域子目录，先跑 `harness install` 初始化 -->"

    domain_names = sorted(
        d.name for d in domains_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )
    if not domain_names:
        return "<!-- 暂无领域子目录 -->"

    lines = []
    for name in domain_names:
        lines.append(f"- [{name}](domains/{name}/README.md)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主刷新函数
# ---------------------------------------------------------------------------

def _refresh_llm_sections(root: Path, playbook_root: Path) -> None:
    """刷新已存在路书文件中的 LLM:* 区段（chg-04：仅对已存在区段刷新）。

    只对有 LLM:* 标记的文件调 LLM 填充；失败时 stderr WARN，不破坏现有内容。
    """
    import os
    import sys

    if os.getenv("CI", "").lower() == "true":
        return

    try:
        from harness_workflow.playbook.llm import (
            NoopProvider,
            PlaybookContext,
            auto_detect_provider,
        )
        from harness_workflow.playbook.domain_inference import infer_domains

        llm = auto_detect_provider()
        if isinstance(llm, NoopProvider):
            # chg-C Step 4.1：NoopProvider fallback 时输出强提示句，让 agent 接力填充
            from harness_workflow.playbook.init import _print_noop_fill_hint
            _print_noop_fill_hint(root)
            return

        # 推断领域
        _, domains = infer_domains(root)
        if not domains:
            return

        context = PlaybookContext(
            project_name=root.name,
            stack=[],
            layout="",
            domains=domains,
            matched_mode="unknown",
        )

        content = None
        try:
            content = llm.generate(context)
        except Exception as e:
            print(f"[llm] WARN: provider failed, falling back to Noop: {e}", file=sys.stderr)
            return

        if content is None:
            return

        # 刷新 overview.md LLM 区段
        overview_md = playbook_root / "overview.md"
        if overview_md.exists():
            try:
                text = overview_md.read_text(encoding="utf-8")
                if "<!-- LLM:OVERVIEW_DESC -->" in text:
                    updated, ok, _ = replace_auto_section(
                        text, "OVERVIEW_DESC", content.overview_description or "", prefix="LLM"
                    )
                    if ok:
                        text = updated
                if "<!-- LLM:TECH_DECISIONS -->" in text:
                    decisions_text = "\n".join(
                        f"- {d}" for d in (content.tech_decisions or [])
                    )
                    updated, ok, _ = replace_auto_section(text, "TECH_DECISIONS", decisions_text, prefix="LLM")
                    if ok:
                        text = updated
                overview_md.write_text(text, encoding="utf-8")
            except Exception as e:
                print(f"[llm] WARN: failed to refresh LLM sections in overview.md: {e}", file=sys.stderr)

        # 刷新各领域 README.md LLM 区段
        domains_dir = playbook_root / "domains"
        if domains_dir.is_dir():
            for domain in domains:
                readme_path = domains_dir / domain / "README.md"
                if not readme_path.exists():
                    continue
                try:
                    text = readme_path.read_text(encoding="utf-8")
                    changed = False
                    if "<!-- LLM:DOMAIN_DESC -->" in text:
                        desc = (content.domain_descriptions or {}).get(domain, "")
                        if desc:
                            updated, ok, _ = replace_auto_section(text, "DOMAIN_DESC", desc, prefix="LLM")
                            if ok:
                                text = updated
                                changed = True
                    if "<!-- LLM:KEYWORDS -->" in text:
                        kws = (content.domain_keywords or {}).get(domain, [])
                        kw_text = ", ".join(kws) if kws else ""
                        if kw_text:
                            updated, ok, _ = replace_auto_section(text, "KEYWORDS", kw_text, prefix="LLM")
                            if ok:
                                text = updated
                                changed = True
                    if changed:
                        readme_path.write_text(text, encoding="utf-8")
                except Exception as e:
                    print(f"[llm] WARN: failed to refresh LLM sections for {domain}: {e}", file=sys.stderr)

        # 刷新 code-map.md LLM:CODE_MAP_KEYWORDS 区段
        code_map_md = playbook_root / "code-map.md"
        if code_map_md.exists():
            try:
                text = code_map_md.read_text(encoding="utf-8")
                if "<!-- LLM:CODE_MAP_KEYWORDS -->" in text:
                    all_kws = []
                    for domain in domains:
                        kws = (content.domain_keywords or {}).get(domain, [])
                        all_kws.extend(kws)
                    kw_text = ", ".join(dict.fromkeys(all_kws))
                    if kw_text:
                        updated, ok, _ = replace_auto_section(
                            text, "CODE_MAP_KEYWORDS", kw_text, prefix="LLM"
                        )
                        if ok:
                            code_map_md.write_text(updated, encoding="utf-8")
            except Exception as e:
                print(f"[llm] WARN: failed to refresh LLM sections in code-map.md: {e}", file=sys.stderr)

    except Exception as e:
        print(f"[llm] WARN: LLM refresh phase failed: {e}", file=sys.stderr)


def playbook_refresh(root: str | Path, dry_run: bool = False, no_llm: bool = False) -> int:
    """刷新路书 5 类 AUTO 区段。

    路径锁定：{root}/artifacts/project/playbooks/（OQ-1=B）

    返回 0（成功）/ 1（路书不存在 / IO 错误 / 配对校验严重失败）。
    """
    root = Path(root).resolve()
    playbook_root = root / PLAYBOOK_ROOT_SUFFIX

    if not playbook_root.is_dir():
        print(
            f"[playbook-refresh] 未找到路书目录 {PLAYBOOK_ROOT_SUFFIX}，"
            "先跑 `harness install` 初始化",
            file=sys.stderr,
        )
        return 1

    total_refreshed = 0
    has_critical_error = False
    diffs: list[str] = []

    # -----------------------------------------------------------------------
    # 辅助：读 / 刷新 / 写（或 dry-run 打 diff）
    # -----------------------------------------------------------------------
    def _refresh_file(fpath: Path, marker: str, new_content: str, label: str) -> bool:
        nonlocal total_refreshed, has_critical_error

        if not fpath.exists():
            print(
                f"[playbook-refresh] WARN: 文件不存在，跳过 {fpath.relative_to(root)}",
                file=sys.stderr,
            )
            return False

        try:
            original = fpath.read_text(encoding="utf-8")
        except IOError as e:
            print(f"[playbook-refresh] ERROR: 读取 {fpath} 失败: {e}", file=sys.stderr)
            has_critical_error = True
            return False

        updated, success, warn = replace_auto_section(original, marker, new_content)

        if warn:
            print(warn, file=sys.stderr)
        if not success:
            return False

        if updated == original:
            # 内容无变化（区段已是最新）
            return True

        rel = str(fpath.relative_to(root))
        if dry_run:
            # 打印 unified diff
            diff_lines = list(difflib.unified_diff(
                original.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
                n=3,
            ))
            if diff_lines:
                diffs.extend(diff_lines)
                print(f"[dry-run] {label} → {rel} (AUTO:{marker}): {len(diff_lines)} diff lines")
        else:
            try:
                fpath.write_text(updated, encoding="utf-8")
                print(f"[playbook-refresh] refreshed {rel} AUTO:{marker}")
                total_refreshed += 1
            except IOError as e:
                print(f"[playbook-refresh] ERROR: 写入 {fpath} 失败: {e}", file=sys.stderr)
                has_critical_error = True
                return False

        return True

    # -----------------------------------------------------------------------
    # 1. AUTO:STACK → architecture.md
    # -----------------------------------------------------------------------
    arch_md = playbook_root / "architecture.md"
    _refresh_file(arch_md, "STACK", _scan_stack(root), "技术栈")

    # -----------------------------------------------------------------------
    # 2. AUTO:SCRIPTS → architecture.md
    # -----------------------------------------------------------------------
    _refresh_file(arch_md, "SCRIPTS", _scan_scripts(root), "常用脚本")

    # -----------------------------------------------------------------------
    # 3. AUTO:LAYOUT → architecture.md
    # -----------------------------------------------------------------------
    _refresh_file(arch_md, "LAYOUT", _scan_layout(root), "目录结构")

    # -----------------------------------------------------------------------
    # 4. AUTO:DOMAIN_LIST → overview.md
    # -----------------------------------------------------------------------
    overview_md = playbook_root / "overview.md"
    _refresh_file(overview_md, "DOMAIN_LIST", _scan_domain_list(playbook_root), "领域列表")

    # -----------------------------------------------------------------------
    # 5. AUTO:DOMAIN_FILES → code-map.md（汇总所有领域的 code.md）
    # -----------------------------------------------------------------------
    code_map_md = playbook_root / "code-map.md"
    domains_dir = playbook_root / "domains"
    if domains_dir.is_dir():
        domain_names = sorted(
            d.name for d in domains_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )
    else:
        domain_names = []

    # code-map.md 中 DOMAIN_FILES = 各领域 code.md 汇总
    code_map_lines = []
    for domain_name in domain_names:
        code_md_path = domains_dir / domain_name / "code.md"
        if code_md_path.exists():
            code_map_lines.append(f"### {domain_name}")
            code_md_content = code_md_path.read_text(encoding="utf-8", errors="replace")
            # 提取 AUTO:DOMAIN_FILES 区段内容
            m = re.search(
                r"<!-- AUTO:DOMAIN_FILES -->(.*?)<!-- /AUTO:DOMAIN_FILES -->",
                code_md_content,
                re.DOTALL,
            )
            if m:
                section_content = m.group(1).strip()
                if section_content:
                    code_map_lines.append(section_content)
                else:
                    code_map_lines.append(f"<!-- {domain_name} 暂无文件列表，先跑 playbook-refresh -->")
            else:
                code_map_lines.append(f"<!-- {domain_name}/code.md 缺少 AUTO:DOMAIN_FILES 区段 -->")
            code_map_lines.append("")
        else:
            code_map_lines.append(f"### {domain_name}")
            code_map_lines.append(f"<!-- {domain_name}/code.md 不存在 -->")
            code_map_lines.append("")

    _refresh_file(
        code_map_md,
        "DOMAIN_FILES",
        "\n".join(code_map_lines),
        "模块索引",
    )

    # -----------------------------------------------------------------------
    # 6. AUTO:DOMAIN_FILES → domains/*/code.md（各领域分别刷新）
    # -----------------------------------------------------------------------
    for domain_name in domain_names:
        code_md_path = domains_dir / domain_name / "code.md"
        domain_files_content = _scan_domain_files(
            domains_dir / domain_name, root, domain_name
        )
        _refresh_file(code_md_path, "DOMAIN_FILES", domain_files_content, f"领域文件[{domain_name}]")

    # -----------------------------------------------------------------------
    # dry-run 输出汇总 diff
    # -----------------------------------------------------------------------
    if dry_run:
        if diffs:
            print("\n--- dry-run diff 汇总 ---")
            print("".join(diffs))
        else:
            print("[dry-run] 所有 AUTO 区段已是最新，无需刷新")
        return 0

    if has_critical_error:
        return 1

    if total_refreshed > 0:
        print(f"[playbook-refresh] 完成：刷新 {total_refreshed} 个 AUTO 区段")
    else:
        print("[playbook-refresh] 所有 AUTO 区段已是最新，无需刷新")

    # -----------------------------------------------------------------------
    # LLM 区段刷新阶段（chg-04：AUTO 区段刷新完成后，对已存在的 LLM 区段填充）
    # chg-D：--no-llm 跳过 LLM 调用，但仍输出 ASSISTANT INSTRUCTION 提示句（让 agent 接力）
    # -----------------------------------------------------------------------
    if not no_llm:
        _refresh_llm_sections(root, playbook_root)
    else:
        # --no-llm 时：跳过 LLM，输出强提示句让 agent 接力填写
        from harness_workflow.playbook.init import _print_noop_fill_hint
        _print_noop_fill_hint(root)

    return 0


# ---------------------------------------------------------------------------
# CLI 入口（tool script 形式）
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="刷新路书 AUTO 区段（req-55（项目路书Playbook体系）/ chg-04）",
    )
    parser.add_argument("--root", default=".", help="仓库根目录")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="打印将要写入的 diff，不落盘",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="跳过 LLM 区段填充阶段（chg-C：与 harness install --no-llm 语义一致）",
    )
    args = parser.parse_args(argv)
    return playbook_refresh(args.root, dry_run=args.dry_run, no_llm=args.no_llm)


if __name__ == "__main__":
    sys.exit(main())
