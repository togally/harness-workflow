"""req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-01（项目描述扫描器 + project-profile 落地）

静态扫描项目根描述文件，产出 ``ProjectProfile`` 数据类与 ``project-profile.md``
渲染文本。**仅本 chg 提供能力**，不接入 ``harness update``（由 chg-02 负责），
不做 briefing 注入（由 chg-03 负责）。

支持文件：
  - ``pyproject.toml`` / ``package.json`` / ``pom.xml`` / ``go.mod`` / ``Cargo.toml``
  - ``README.md`` / ``README.rst`` / ``CLAUDE.md`` / ``AGENTS.md``（仅取首 H1 作为 project_headline）

公开 API：
  - ``ProjectProfile``：结构化字段数据类
  - ``build_project_profile(root: Path) -> ProjectProfile``：扫 → 结构化
  - ``render_project_profile(profile, *, now) -> str``：渲染为 Markdown 文本
  - ``load_project_profile(path: Path) -> ProjectProfile | None``：从落盘 profile 反向解析
  - ``write_project_profile(root: Path) -> Path``：顶层入口（扫 → 渲染 → 写盘）
"""

from __future__ import annotations

import json
import re
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .workflow_helpers import _managed_hash

# req-32 / chg-01：依赖截断上限，避免 profile 过长；后续可按需调整
DEPS_TOP_N: int = 20

# 生成 profile 的相对路径（本 chg 约定，chg-02 的 update 接入保持一致）
PROFILE_REL_PATH: str = ".workflow/context/project-profile.md"


@dataclass
class ProjectProfile:
    """req-32 / chg-01：项目描述结构化字段。

    所有字段初始均为空，按发现的文件逐步填充；未识别时 ``language='unknown'``。
    """

    package_name: str = ""
    language: str = "unknown"
    deps_top: list[str] = field(default_factory=list)
    entrypoints: list[str] = field(default_factory=list)
    stack_tags: list[str] = field(default_factory=list)
    project_headline: str = ""
    parse_errors: list[str] = field(default_factory=list)


# -----------------------------
# 各描述文件解析（不抛异常，异常收集到 parse_errors）
# -----------------------------


def _parse_pyproject(path: Path, profile: ProjectProfile) -> None:
    """req-32 / chg-01 / Step 1：解析 pyproject.toml（PEP 621 / poetry 双兼容）。"""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        profile.parse_errors.append(f"pyproject.toml: {exc}")
        return

    project = data.get("project") or {}
    tool = data.get("tool") or {}
    poetry = tool.get("poetry") if isinstance(tool, dict) else None

    name = project.get("name") or (poetry or {}).get("name") or ""
    if name:
        profile.package_name = str(name)

    profile.language = "python"

    deps = project.get("dependencies") or []
    if isinstance(deps, list):
        for dep in deps[:DEPS_TOP_N]:
            profile.deps_top.append(str(dep))
    elif isinstance(deps, dict):
        for k, v in list(deps.items())[:DEPS_TOP_N]:
            profile.deps_top.append(f"{k} {v}".strip())

    if isinstance(poetry, dict):
        poetry_deps = poetry.get("dependencies") or {}
        if isinstance(poetry_deps, dict):
            for k, v in list(poetry_deps.items())[:DEPS_TOP_N]:
                if k == "python":
                    continue
                profile.deps_top.append(f"{k} {v}".strip())

    scripts = project.get("scripts") or {}
    if isinstance(scripts, dict):
        for k, v in scripts.items():
            profile.entrypoints.append(f"{k}={v}")

    # stack tag：有 pyproject 即 python+pyproject；若有 poetry 再加 python+poetry
    if "python+pyproject" not in profile.stack_tags:
        profile.stack_tags.append("python+pyproject")
    if isinstance(poetry, dict) and "python+poetry" not in profile.stack_tags:
        profile.stack_tags.append("python+poetry")


def _parse_package_json(path: Path, profile: ProjectProfile) -> None:
    """req-32 / chg-01 / Step 1：解析 package.json。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        profile.parse_errors.append(f"package.json: {exc}")
        return

    name = data.get("name") or ""
    if name:
        profile.package_name = str(name)

    profile.language = "nodejs"

    deps = data.get("dependencies") or {}
    dev_deps = data.get("devDependencies") or {}
    if isinstance(deps, dict):
        for k, v in list(deps.items())[:DEPS_TOP_N]:
            profile.deps_top.append(f"{k} {v}".strip())

    scripts = data.get("scripts") or {}
    if isinstance(scripts, dict):
        for k, v in scripts.items():
            profile.entrypoints.append(f"{k}={v}")
    main = data.get("main")
    if main:
        profile.entrypoints.append(f"main={main}")

    if "nodejs" not in profile.stack_tags:
        profile.stack_tags.append("nodejs")
    # TS 存在标签
    if isinstance(dev_deps, dict) and "typescript" in dev_deps:
        profile.stack_tags.append("node+ts")
    elif isinstance(deps, dict) and "typescript" in deps:
        profile.stack_tags.append("node+ts")


def _parse_pom_xml(path: Path, profile: ProjectProfile) -> None:
    """req-32 / chg-01 / Step 2：解析 Maven pom.xml。"""
    try:
        tree = ET.parse(path)
    except Exception as exc:  # noqa: BLE001
        profile.parse_errors.append(f"pom.xml: {exc}")
        return

    root = tree.getroot()
    # 处理 Maven 命名空间
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    def _find(tag: str, parent: ET.Element | None = None) -> ET.Element | None:
        parent = parent if parent is not None else root
        return parent.find(f"{ns}{tag}")

    artifact = _find("artifactId")
    if artifact is not None and artifact.text:
        profile.package_name = artifact.text.strip()

    profile.language = "java"

    deps_node = _find("dependencies")
    if deps_node is not None:
        for dep in deps_node.findall(f"{ns}dependency")[:DEPS_TOP_N]:
            group = _find("groupId", dep)
            art = _find("artifactId", dep)
            ver = _find("version", dep)
            gid = (group.text or "").strip() if group is not None else ""
            aid = (art.text or "").strip() if art is not None else ""
            vid = (ver.text or "").strip() if ver is not None else ""
            profile.deps_top.append(f"{gid}:{aid}:{vid}".strip(":"))

    if "java+maven" not in profile.stack_tags:
        profile.stack_tags.append("java+maven")


def _parse_go_mod(path: Path, profile: ProjectProfile) -> None:
    """req-32 / chg-01 / Step 2：解析 go.mod（正则提取 module + require 块）。"""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        profile.parse_errors.append(f"go.mod: {exc}")
        return

    profile.language = "go"

    m = re.search(r"^\s*module\s+(\S+)\s*$", content, flags=re.MULTILINE)
    if m:
        module_path = m.group(1).strip()
        # 取最后一段作为 package_name
        profile.package_name = module_path.rsplit("/", 1)[-1]

    # 解析 require ( ... ) 与单行 require
    deps: list[str] = []
    block_match = re.search(r"require\s*\(([^)]*)\)", content, flags=re.DOTALL)
    if block_match:
        for line in block_match.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                deps.append(f"{parts[0]} {parts[1]}")
    for m in re.finditer(r"^\s*require\s+(\S+)\s+(\S+)\s*$", content, flags=re.MULTILINE):
        deps.append(f"{m.group(1)} {m.group(2)}")

    profile.deps_top.extend(deps[:DEPS_TOP_N])

    if "go-module" not in profile.stack_tags:
        profile.stack_tags.append("go-module")


def _parse_cargo_toml(path: Path, profile: ProjectProfile) -> None:
    """req-32 / chg-01 / Step 2：解析 Cargo.toml。"""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        profile.parse_errors.append(f"Cargo.toml: {exc}")
        return

    pkg = data.get("package") or {}
    name = pkg.get("name") or ""
    if name:
        profile.package_name = str(name)

    profile.language = "rust"

    deps = data.get("dependencies") or {}
    if isinstance(deps, dict):
        for k, v in list(deps.items())[:DEPS_TOP_N]:
            if isinstance(v, dict):
                ver = v.get("version", "")
                profile.deps_top.append(f"{k} {ver}".strip())
            else:
                profile.deps_top.append(f"{k} {v}".strip())

    if "rust-cargo" not in profile.stack_tags:
        profile.stack_tags.append("rust-cargo")


def _extract_first_h1(path: Path) -> str:
    """提取首个一级标题（Markdown ``# ...`` 或 rst 下划线形式的简化版）。"""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:  # noqa: BLE001
        return ""
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        # rst: 标题下一行为 ==== / ---- 连续符号
        if idx + 1 < len(lines):
            under = lines[idx + 1].strip()
            if under and len(under) >= 3 and set(under) <= {"=", "-"} and stripped:
                return stripped
    return ""


def _parse_readme_like(path: Path, profile: ProjectProfile) -> None:
    """README / CLAUDE / AGENTS：只取首个 H1 作为 project_headline（若尚未设置）。"""
    if profile.project_headline:
        return
    headline = _extract_first_h1(path)
    if headline:
        profile.project_headline = headline


# -----------------------------
# 顶层扫描入口
# -----------------------------


def build_project_profile(root: Path) -> ProjectProfile:
    """req-32 / chg-01 / Step 1：扫描 ``root`` 并返回结构化 ``ProjectProfile``。

    存在即解析，缺失即跳过；所有解析异常不外抛，写入 ``profile.parse_errors``。
    """
    profile = ProjectProfile()
    root = Path(root)

    handlers: list[tuple[str, Callable[[Path, ProjectProfile], None]]] = [
        ("pyproject.toml", _parse_pyproject),
        ("package.json", _parse_package_json),
        ("pom.xml", _parse_pom_xml),
        ("go.mod", _parse_go_mod),
        ("Cargo.toml", _parse_cargo_toml),
        ("README.md", _parse_readme_like),
        ("README.rst", _parse_readme_like),
        ("CLAUDE.md", _parse_readme_like),
        ("AGENTS.md", _parse_readme_like),
    ]

    for rel, handler in handlers:
        p = root / rel
        if p.exists() and p.is_file():
            handler(p, profile)

    # 依赖去重 + 截断
    seen: set[str] = set()
    dedup: list[str] = []
    for dep in profile.deps_top:
        if dep in seen:
            continue
        seen.add(dep)
        dedup.append(dep)
        if len(dedup) >= DEPS_TOP_N:
            break
    profile.deps_top = dedup

    return profile
