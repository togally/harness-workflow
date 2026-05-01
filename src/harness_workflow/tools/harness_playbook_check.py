"""harness playbook-check 子命令（req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-05（harness playbook-check 子命令））

req-56 / chg-05 注释更新：_AUTO_OPEN_RE / _AUTO_CLOSE_RE 正则扩展覆盖 LLM 区段（<!-- LLM:* -->），
行为基本不变，只扩正则面（AUTO|LLM 命名空间，issue 字符串前缀不变，向后兼容）。

chg-C 注释更新：新增 USER 区段支持（<!-- USER:* -->）。
  - USER 区段永不报漂移（人工随时可改）
  - USER 区段 marker 完整性仍校验（SEGMENT_UNPAIRED）
  - K-01 keyword coverage 扩展到所有 LLM:* 区段（不只 README 职责描述）

检测 artifacts/project/playbooks/ 内路书漂移 + 契约校验（OQ-1=B 路径定位）：

  D-01 依赖漂移（DEPENDENCY_DRIFT）
  D-02 scripts 漂移（SCRIPTS_DRIFT）
  D-03 模块目录漂移（MODULE_DIR_DRIFT）
  D-04 code-map 互引漂移（CODEMAP_REF_DRIFT / C-05）
  D-05 code.md 引用失效（CODE_MD_REF_BROKEN）
  D-06 README 依赖链接失效（README_DEP_BROKEN）
  K-01 关键词覆盖空（KEYWORD_COVERAGE）
  C-01 AUTO/LLM/USER 区段配对（SEGMENT_UNPAIRED）
  C-03 path schema 锁定（PATH_SCHEMA_VIOLATION）
  C-05 domains 互引一致性（DOMAIN_SUBDIR_MISMATCH）
  AUTO/LLM 区段哈希漂移（OQ-5=A 路书只读软约束 + CI 兜底）
  USER 区段永不报漂移（人工随时可改）

不调 LLM（纯静态分析，spec §四明示）。
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

from harness_workflow.tools.harness_playbook_refresh import IGNORE_DIRS


# ---------------------------------------------------------------------------
# 路径锁定（OQ-1=B）
# ---------------------------------------------------------------------------

PLAYBOOK_ROOT_SUFFIX = "artifacts/project/playbooks"

# 裸路径模式：artifacts/playbooks/（无 project/ 中间层）→ 路径合规失败
_BAD_PATH_PATTERN = re.compile(r"artifacts/playbooks/")

# AUTO/LLM 区段开/闭标记正则（req-56 / chg-05 扩展：覆盖 AUTO 和 LLM 两个命名空间）
_AUTO_OPEN_RE = re.compile(r"<!--\s*(AUTO|LLM):(\w+)\s*-->")
_AUTO_CLOSE_RE = re.compile(r"<!--\s*/(AUTO|LLM):(\w+)\s*-->")

# USER 区段开/闭标记正则（chg-C 新增：USER 区段永不报漂移，只校验配对完整性）
_USER_OPEN_RE = re.compile(r"<!--\s*USER:(\w+)\s*-->")
_USER_CLOSE_RE = re.compile(r"<!--\s*/USER:(\w+)\s*-->")


# ---------------------------------------------------------------------------
# 结果类型
# ---------------------------------------------------------------------------

class CheckResult(NamedTuple):
    passed: bool
    issues: list[str]


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _find_auto_segments(content: str) -> list[tuple[str, str]]:
    """提取所有 AUTO/LLM 区段，返回 [(marker_name, segment_content), ...]。
    只返回配对完整的区段（req-56 / chg-05：扩展覆盖 LLM 命名空间）。"""
    segments = []
    pattern = re.compile(
        r"<!--\s*(?:AUTO|LLM):(\w+)\s*-->(.*?)<!--\s*/(?:AUTO|LLM):\1\s*-->",
        re.DOTALL,
    )
    for m in pattern.finditer(content):
        segments.append((m.group(1), m.group(2)))
    return segments


def _check_auto_pairs(content: str) -> list[str]:
    """C-01 / C-04：检测 AUTO/LLM/USER 区段配对是否完整，返回缺失配对的 issue 列表。
    req-56 / chg-05：正则扩展覆盖 LLM 命名空间，issue 字符串前缀不变（向后兼容）。
    chg-C：新增 USER 命名空间配对校验（USER 区段永不报漂移，但 marker 不配对仍报 SEGMENT_UNPAIRED）。"""
    # _AUTO_OPEN_RE / _AUTO_CLOSE_RE 返回 (namespace, name) 两元组（覆盖 AUTO + LLM）
    open_markers = set(_AUTO_OPEN_RE.findall(content))
    close_markers = set(_AUTO_CLOSE_RE.findall(content))
    issues = []
    for ns, name in open_markers - close_markers:
        issues.append(f"SEGMENT_UNPAIRED: <!-- {ns}:{name} --> 缺少对应 <!-- /{ns}:{name} -->")
    for ns, name in close_markers - open_markers:
        issues.append(f"SEGMENT_UNPAIRED: <!-- /{ns}:{name} --> 缺少对应 <!-- {ns}:{name} -->")

    # USER 区段配对校验（chg-C：永不报漂移，但 marker 不配对仍报 SEGMENT_UNPAIRED）
    user_open_names = set(_USER_OPEN_RE.findall(content))
    user_close_names = set(_USER_CLOSE_RE.findall(content))
    for name in user_open_names - user_close_names:
        issues.append(f"SEGMENT_UNPAIRED: <!-- USER:{name} --> 缺少对应 <!-- /USER:{name} -->")
    for name in user_close_names - user_open_names:
        issues.append(f"SEGMENT_UNPAIRED: <!-- /USER:{name} --> 缺少对应 <!-- USER:{name} -->")

    return issues


# ---------------------------------------------------------------------------
# D-01 依赖漂移：pyproject.toml / package.json 新 dep 未在 AUTO:STACK 中提及
# ---------------------------------------------------------------------------

def check_d01_dependency_drift(root: Path, playbook_root: Path) -> CheckResult:
    """D-01 DEPENDENCY_DRIFT：扫描 pyproject.toml / package.json deps，
    对比 architecture.md AUTO:STACK 区段当前内容；deps 新增但区段未提 → 漂移。"""
    issues: list[str] = []

    arch_md = playbook_root / "architecture.md"
    if not arch_md.exists():
        return CheckResult(True, [])

    arch_content = arch_md.read_text(encoding="utf-8", errors="replace")

    # 提取 AUTO:STACK 区段内容
    m = re.search(r"<!-- AUTO:STACK -->(.*?)<!-- /AUTO:STACK -->", arch_content, re.DOTALL)
    stack_content = m.group(1) if m else ""

    # 扫描 pyproject.toml deps
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8", errors="replace")
        deps = re.findall(r'^([a-zA-Z0-9_\-]+)\s*=\s*["\'^~>=!<]', text, re.MULTILINE)
        skip_keys = {"python", "name", "version", "description", "authors", "readme",
                     "license", "requires-python", "classifiers", "homepage", "repository"}
        for dep in deps:
            if dep.lower() in skip_keys:
                continue
            if dep.lower() not in stack_content.lower():
                issues.append(
                    f"dependency drift (D-01): '{dep}' 在 pyproject.toml 中声明但 "
                    f"architecture.md AUTO:STACK 区段未提及 → 建议跑 `harness playbook-refresh`"
                )

    # 扫描 package.json deps
    package_json = root / "package.json"
    if package_json.exists():
        try:
            import json
            data = json.loads(package_json.read_text(encoding="utf-8"))
            all_deps = list((data.get("dependencies") or {}).keys()) + \
                       list((data.get("devDependencies") or {}).keys())
            for dep in all_deps[:20]:
                if dep.lower() not in stack_content.lower():
                    issues.append(
                        f"dependency drift (D-01): '{dep}' 在 package.json 中声明但 "
                        f"architecture.md AUTO:STACK 区段未提及 → 建议跑 `harness playbook-refresh`"
                    )
        except Exception:
            pass

    return CheckResult(len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# D-02 scripts 漂移：pyproject.toml scripts / Makefile 新 script 未在 AUTO:SCRIPTS 中提及
# ---------------------------------------------------------------------------

def check_d02_scripts_drift(root: Path, playbook_root: Path) -> CheckResult:
    """D-02 SCRIPTS_DRIFT：扫描 pyproject.toml scripts / Makefile，
    对比 architecture.md AUTO:SCRIPTS 区段当前内容；新增 → 漂移。"""
    issues: list[str] = []

    arch_md = playbook_root / "architecture.md"
    if not arch_md.exists():
        return CheckResult(True, [])

    arch_content = arch_md.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<!-- AUTO:SCRIPTS -->(.*?)<!-- /AUTO:SCRIPTS -->", arch_content, re.DOTALL)
    scripts_content = m.group(1) if m else ""

    # 扫描 pyproject.toml scripts
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8", errors="replace")
        script_entries = re.findall(r'^(\w[\w\-]+)\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        for name, target in script_entries:
            # 看起来是 entrypoint（含 : 或 .）
            if (":" in target or "." in target) and name.lower() not in scripts_content.lower():
                issues.append(
                    f"scripts drift (D-02): '{name}' 在 pyproject.toml scripts 中声明但 "
                    f"architecture.md AUTO:SCRIPTS 区段未提及 → 建议跑 `harness playbook-refresh`"
                )

    # 扫描 Makefile targets
    makefile = root / "Makefile"
    if makefile.exists():
        text = makefile.read_text(encoding="utf-8", errors="replace")
        targets = re.findall(r'^([a-zA-Z][a-zA-Z0-9_\-]*)\s*:', text, re.MULTILINE)
        visible = [t for t in targets if not t.startswith(".") and t not in ("PHONY",)]
        for t in visible[:10]:
            if t.lower() not in scripts_content.lower():
                issues.append(
                    f"scripts drift (D-02): Makefile target '{t}' 未在 "
                    f"architecture.md AUTO:SCRIPTS 区段中提及 → 建议跑 `harness playbook-refresh`"
                )

    return CheckResult(len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# D-03 模块目录漂移：源码新增模块但 domains/ 无对应文件夹
# ---------------------------------------------------------------------------

def check_d03_module_dir_drift(root: Path, playbook_root: Path) -> CheckResult:
    """D-03 MODULE_DIR_DRIFT：扫描 src/{pkg}/{sub}/ 等领域目录，
    对比 domains/ 子目录；源码新增但 domains/ 无对应 → 漂移。"""
    issues: list[str] = []

    domains_dir = playbook_root / "domains"
    if not domains_dir.is_dir():
        return CheckResult(True, [])

    existing_domains = {
        d.name for d in domains_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    }

    # 扫描 src/{pkg}/{sub}/ 候选模块目录
    src_dir = root / "src"
    candidate_modules: set[str] = set()
    if src_dir.is_dir():
        for pkg_dir in src_dir.iterdir():
            if not pkg_dir.is_dir() or pkg_dir.name.startswith(".") or pkg_dir.name == "__pycache__":
                continue
            for sub_dir in pkg_dir.iterdir():
                if sub_dir.is_dir() and not sub_dir.name.startswith("_") and \
                   not sub_dir.name.startswith(".") and sub_dir.name != "__pycache__" and \
                   sub_dir.name not in IGNORE_DIRS:
                    candidate_modules.add(sub_dir.name)

    # 扫描 src/modules/* / src/domains/* / app/*
    for scan_path in [root / "src" / "modules", root / "src" / "domains", root / "app"]:
        if scan_path.is_dir():
            for d in scan_path.iterdir():
                if d.is_dir() and not d.name.startswith(".") and d.name not in IGNORE_DIRS:
                    candidate_modules.add(d.name)

    # 新增模块但 domains/ 无对应
    for module in sorted(candidate_modules):
        if module not in existing_domains:
            issues.append(
                f"module dir drift (D-03): 源码模块 '{module}' 存在但 "
                f"domains/{module}/ 路书目录不存在 → 建议新增领域或跑 `harness install`"
            )

    return CheckResult(len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# D-04 code-map 互引漂移 / C-05 domains 互引一致性
# ---------------------------------------------------------------------------

def check_d04_codemap_consistency(root: Path, playbook_root: Path) -> CheckResult:
    """D-04 CODEMAP_REF_DRIFT / C-05 DOMAIN_SUBDIR_MISMATCH：
    domains/ 子目录 ↔ code-map.md AUTO:DOMAIN_FILES 区段登记互引完整性。"""
    issues: list[str] = []

    domains_dir = playbook_root / "domains"
    code_map_md = playbook_root / "code-map.md"

    if not code_map_md.exists():
        return CheckResult(True, [])

    code_map_content = code_map_md.read_text(encoding="utf-8", errors="replace")

    # 提取 AUTO:DOMAIN_FILES 区段内容
    m = re.search(r"<!-- AUTO:DOMAIN_FILES -->(.*?)<!-- /AUTO:DOMAIN_FILES -->",
                  code_map_content, re.DOTALL)
    domain_files_content = m.group(1) if m else ""

    # 提取 code-map.md 中登记的领域（### {领域名} 标题行）
    registered_in_codemap = set(
        re.findall(r'^###\s+(\S+)', domain_files_content, re.MULTILINE)
    )

    # 实际 domains/ 子目录
    actual_domains: set[str] = set()
    if domains_dir.is_dir():
        actual_domains = {
            d.name for d in domains_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        }

    # 双向检测
    only_in_dirs = actual_domains - registered_in_codemap
    only_in_codemap = registered_in_codemap - actual_domains

    for domain in sorted(only_in_dirs):
        issues.append(
            f"codemap ref drift (D-04 / C-05): domains/{domain}/ 存在但 "
            f"code-map.md AUTO:DOMAIN_FILES 未登记 → DOMAIN_SUBDIR_MISMATCH"
        )
    for domain in sorted(only_in_codemap):
        issues.append(
            f"codemap ref drift (D-04 / C-05): code-map.md 登记了 '{domain}' 但 "
            f"domains/{domain}/ 目录不存在 → DOMAIN_SUBDIR_MISMATCH"
        )

    return CheckResult(len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# D-05 code.md 引用失效
# ---------------------------------------------------------------------------

def check_d05_codefile_path_validity(root: Path, playbook_root: Path) -> CheckResult:
    """D-05 CODE_MD_REF_BROKEN：扫 domains/*/code.md 内 '- `src/...' 行，
    断言路径 os.path.exists；不存在 → 漂移。"""
    issues: list[str] = []

    domains_dir = playbook_root / "domains"
    if not domains_dir.is_dir():
        return CheckResult(True, [])

    # 匹配 `- `path`：...` 或 `- path：...` 格式的路径行
    path_line_re = re.compile(r"^-\s+`([^`]+)`")

    for domain_dir in sorted(domains_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        code_md = domain_dir / "code.md"
        if not code_md.exists():
            continue
        content = code_md.read_text(encoding="utf-8", errors="replace")
        for line in content.splitlines():
            m = path_line_re.match(line.strip())
            if not m:
                continue
            ref_path = m.group(1)
            # 跳过注释行（以 <!-- 开头）
            if ref_path.startswith("<!--"):
                continue
            # 跳过 TODO 占位
            if "TODO" in ref_path:
                continue
            full_path = root / ref_path
            if not full_path.exists():
                issues.append(
                    f"code.md ref broken (D-05): {domain_dir.name}/code.md 引用的路径 "
                    f"'{ref_path}' 不存在 → CODE_MD_REF_BROKEN"
                )

    return CheckResult(len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# D-06 README 依赖链接失效
# ---------------------------------------------------------------------------

def check_d06_readme_dep_link(root: Path, playbook_root: Path) -> CheckResult:
    """D-06 README_DEP_BROKEN：扫 domains/*/README.md 中 '## 依赖领域' 节，
    断言对应 domains/{dep}/ 目录存在；不存在 → 漂移。"""
    issues: list[str] = []

    domains_dir = playbook_root / "domains"
    if not domains_dir.is_dir():
        return CheckResult(True, [])

    for domain_dir in sorted(domains_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        readme = domain_dir / "README.md"
        if not readme.exists():
            continue
        content = readme.read_text(encoding="utf-8", errors="replace")

        # 定位 ## 依赖领域 节
        dep_section_m = re.search(
            r"##\s*依赖领域\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
        )
        if not dep_section_m:
            continue
        dep_section = dep_section_m.group(1)

        # 跳过 TODO 占位
        if "TODO" in dep_section and dep_section.strip().startswith("<!--"):
            continue

        # 提取依赖名称（支持 "依赖：payment, user" 格式 + "- payment" bullet）
        dep_names: list[str] = []
        # bullet 格式：- domain_name
        dep_names.extend(re.findall(r'^-\s+(\S+)', dep_section, re.MULTILINE))
        # 行内格式：依赖：xxx, yyy 或 依赖: xxx, yyy
        inline_m = re.search(r'依赖[：:]\s*(.+)', dep_section)
        if inline_m:
            raw_deps = inline_m.group(1)
            dep_names.extend(re.split(r'[,，\s]+', raw_deps.strip()))

        for dep_name in dep_names:
            dep_name = dep_name.strip().strip("。").strip()
            if not dep_name or dep_name.startswith("<!--") or "TODO" in dep_name:
                continue
            dep_dir = domains_dir / dep_name
            if not dep_dir.is_dir():
                issues.append(
                    f"README dep link broken (D-06): {domain_dir.name}/README.md 依赖领域 "
                    f"'{dep_name}' 但 domains/{dep_name}/ 不存在 → README_DEP_BROKEN"
                )

    return CheckResult(len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# K-01 关键词覆盖检测
# ---------------------------------------------------------------------------

def _is_llm_section_empty(section_content: str) -> bool:
    """检测 LLM 区段内容是否仍为 TODO 占位（空 / ≤ 10 字节 / 仅 TODO 注释）。"""
    stripped = section_content.strip()
    if len(stripped) <= 10:
        return True
    # 仅含 <!-- LLM:* --> 和/或 <!-- TODO: ... --> 注释行
    # 去掉所有注释行后看是否为空
    non_comment = re.sub(r'<!--.*?-->', '', stripped, flags=re.DOTALL).strip()
    if not non_comment:
        return True
    return False


def check_k01_keyword_coverage(root: Path, playbook_root: Path) -> CheckResult:
    """K-01 KEYWORD_COVERAGE：扫 domains/*/README.md 的 '## 职责描述' 节，
    全空 / 内容 ≤ 10 字节 / 仅 TODO 占位 → 警告。
    chg-C 扩展：同时扫 domains/*/README.md 中 LLM:DOMAIN_DESC 区段（与职责描述节等效）。"""
    issues: list[str] = []

    domains_dir = playbook_root / "domains"
    if not domains_dir.is_dir():
        return CheckResult(True, [])

    for domain_dir in sorted(domains_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        readme = domain_dir / "README.md"
        if not readme.exists():
            continue
        content = readme.read_text(encoding="utf-8", errors="replace")

        # 定位 ## 职责描述 节
        desc_m = re.search(
            r"##\s*职责描述\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
        )
        if not desc_m:
            issues.append(
                f"empty keywords (K-01): {domain_dir.name}/README.md 缺少 ## 职责描述 节 → KEYWORD_COVERAGE"
            )
            continue

        desc_content = desc_m.group(1).strip()

        # chg-C：优先检查 LLM:DOMAIN_DESC 区段内容（若存在）
        llm_desc_m = re.search(
            r"<!--\s*LLM:DOMAIN_DESC\s*-->(.*?)<!--\s*/LLM:DOMAIN_DESC\s*-->",
            desc_content, re.DOTALL
        )
        if llm_desc_m:
            inner = llm_desc_m.group(1)
            if _is_llm_section_empty(inner):
                issues.append(
                    f"empty keywords (K-01): {domain_dir.name}/README.md LLM:DOMAIN_DESC 内容为空或仅 TODO "
                    f"→ KEYWORD_COVERAGE（建议填写真实职责描述）"
                )
            continue

        # 旧式：区段外的职责描述内容
        is_empty = len(desc_content) <= 10
        is_todo = desc_content.startswith("<!--") and "TODO" in desc_content
        is_only_todo = bool(re.match(r'^<!--\s*TODO', desc_content))
        if is_empty or is_todo or is_only_todo:
            issues.append(
                f"empty keywords (K-01): {domain_dir.name}/README.md ## 职责描述 内容为空或仅 TODO "
                f"→ KEYWORD_COVERAGE（建议填写真实职责描述）"
            )

    return CheckResult(len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# C-01 / C-04 AUTO 区段配对校验
# ---------------------------------------------------------------------------

def _enumerate_playbook_files(playbook_root: Path) -> list[Path]:
    """枚举受管路书文件清单（C-01/C-04 扫描范围，chg-F bug-3）。

    只扫：
      - artifacts/project/playbooks/{overview,architecture,runbook,code-map}.md
      - artifacts/project/playbooks/domains/*/{README,code,data-model,notes}.md

    跳过 .workflow/ 路径下的任何 .md 文件（那是 harness skill 文件不是路书）。
    """
    files: list[Path] = []
    top_level_names = {"overview.md", "architecture.md", "runbook.md", "code-map.md"}
    for name in sorted(top_level_names):
        p = playbook_root / name
        if p.exists():
            files.append(p)

    domains_dir = playbook_root / "domains"
    if domains_dir.is_dir():
        domain_file_names = {"README.md", "code.md", "data-model.md", "notes.md"}
        for domain_dir in sorted(domains_dir.iterdir()):
            if not domain_dir.is_dir() or domain_dir.name.startswith("."):
                continue
            for fname in sorted(domain_file_names):
                p = domain_dir / fname
                if p.exists():
                    files.append(p)

    return files


def check_c01_auto_segment_pairs(root: Path, playbook_root: Path) -> CheckResult:
    """C-01 / C-04 SEGMENT_UNPAIRED：受管路书文件中 AUTO:X 与 /AUTO:X 必须配对。

    chg-F bug-3：只扫真正的路书文件（overview/architecture/runbook/code-map + domains/*/*）；
    跳过 .workflow/ 路径（harness skill 文件，示例 marker 不应误报）。
    """
    issues: list[str] = []

    if not playbook_root.is_dir():
        return CheckResult(True, [])

    for md_file in _enumerate_playbook_files(playbook_root):
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        pair_issues = _check_auto_pairs(content)
        for issue in pair_issues:
            try:
                rel = md_file.relative_to(playbook_root.parent.parent.parent)
            except ValueError:
                rel = md_file
            issues.append(f"{rel}: {issue}")

    return CheckResult(len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# C-03 path schema 锁定
# ---------------------------------------------------------------------------

def check_c03_path_schema(root: Path, playbook_root: Path) -> CheckResult:
    """C-03 PATH_SCHEMA_VIOLATION：路书文件中不得出现裸 artifacts/playbooks/（无 project/ 中间层）。"""
    issues: list[str] = []

    target_files = [
        playbook_root / "code-map.md",
        playbook_root / "architecture.md",
        root / "CLAUDE.md",
    ]

    for fpath in target_files:
        if not fpath.exists():
            continue
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = _BAD_PATH_PATTERN.findall(content)
        if matches:
            try:
                rel = fpath.relative_to(root)
            except ValueError:
                rel = fpath
            issues.append(
                f"path schema violation (C-03): {rel} 中出现裸路径 'artifacts/playbooks/'（缺少 project/ 中间层）"
                f" → PATH_SCHEMA_VIOLATION，应改为 'artifacts/project/playbooks/'"
            )

    return CheckResult(len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# C-05 domains 互引一致性（独立契约层封装，复用 D-04 逻辑）
# ---------------------------------------------------------------------------

def check_c05_domain_consistency(root: Path, playbook_root: Path) -> CheckResult:
    """C-05 DOMAIN_SUBDIR_MISMATCH：domains/ 子目录与 code-map.md 登记双向互引完整性。
    独立封装便于 harness validate --contract playbook-layout 复用。"""
    # 直接复用 D-04 逻辑
    return check_d04_codemap_consistency(root, playbook_root)


# ---------------------------------------------------------------------------
# AUTO 区段哈希漂移检测（OQ-5=A 关键兜底）
# ---------------------------------------------------------------------------

def check_auto_segment_hash_drift(root: Path, playbook_root: Path) -> CheckResult:
    """OQ-5=A 关键兜底：检测 AUTO 区段是否被手动修改但未跑 refresh。

    方法：
    1. 读当前路书文件的 AUTO 区段内容
    2. 调 playbook_refresh dry-run（渲染"应该写入什么"）
    3. 对比哈希：当前 ≠ 期望 → AUTO segment drift detected
    """
    issues: list[str] = []

    if not playbook_root.is_dir():
        return CheckResult(True, [])

    # 导入 refresh 的扫描函数（复用，不写盘）
    try:
        from harness_workflow.tools.harness_playbook_refresh import (
            _scan_stack, _scan_scripts, _scan_layout,
            _scan_domain_list, _scan_domain_files,
            replace_auto_section,
        )
    except ImportError:
        # 回退：跳过哈希检测
        return CheckResult(True, ["WARN: 无法导入 harness_playbook_refresh，跳过 AUTO 段哈希漂移检测"])

    def _seg_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _extract_seg(file_content: str, marker: str) -> str | None:
        """提取 AUTO 区段内容（不含标记行本身）。"""
        m = re.search(
            re.escape(f"<!-- AUTO:{marker} -->") + r"(.*?)" + re.escape(f"<!-- /AUTO:{marker} -->"),
            file_content, re.DOTALL,
        )
        return m.group(1) if m else None

    # architecture.md 的 STACK / SCRIPTS / LAYOUT
    arch_md = playbook_root / "architecture.md"
    if arch_md.exists():
        arch_content = arch_md.read_text(encoding="utf-8", errors="replace")
        for marker, scan_fn in [
            ("STACK", lambda: _scan_stack(root)),
            ("SCRIPTS", lambda: _scan_scripts(root)),
            ("LAYOUT", lambda: _scan_layout(root)),
        ]:
            current_seg = _extract_seg(arch_content, marker)
            if current_seg is None:
                continue  # 标记缺失由 C-04 检测
            expected_content = scan_fn()
            # 期望的区段内容：\n + content.rstrip(\n) + \n
            expected_seg = "\n" + expected_content.rstrip("\n") + "\n"
            if _seg_hash(current_seg) != _seg_hash(expected_seg):
                issues.append(
                    f"AUTO segment drift detected: architecture.md AUTO:{marker} 区段内容与 "
                    f"refresh 期望值不一致（可能被手动修改），建议跑 `harness playbook-refresh`"
                )

    # overview.md 的 DOMAIN_LIST
    overview_md = playbook_root / "overview.md"
    if overview_md.exists():
        overview_content = overview_md.read_text(encoding="utf-8", errors="replace")
        current_seg = _extract_seg(overview_content, "DOMAIN_LIST")
        if current_seg is not None:
            expected_content = _scan_domain_list(playbook_root)
            expected_seg = "\n" + expected_content.rstrip("\n") + "\n"
            if _seg_hash(current_seg) != _seg_hash(expected_seg):
                issues.append(
                    f"AUTO segment drift detected: overview.md AUTO:DOMAIN_LIST 区段内容与 "
                    f"refresh 期望值不一致（可能被手动修改），建议跑 `harness playbook-refresh`"
                )

    # 注意：code-map.md 的 DOMAIN_FILES 是从各 domains/*/code.md 聚合而来，
    # 其期望值依赖 refresh 的执行顺序（step5 先于 step6），直接对比会产生误报。
    # code-map.md 的互引一致性由 D-04/C-05 负责检测，此处跳过哈希对比。

    return CheckResult(len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

#: 全量 10 类检测函数（含 C-05 独立封装 + AUTO 哈希漂移）
_ALL_CHECKS = [
    ("D-01 依赖漂移", check_d01_dependency_drift),
    ("D-02 scripts 漂移", check_d02_scripts_drift),
    ("D-03 模块目录漂移", check_d03_module_dir_drift),
    ("D-04 code-map 互引漂移", check_d04_codemap_consistency),
    ("D-05 code.md 引用失效", check_d05_codefile_path_validity),
    ("D-06 README 依赖链接失效", check_d06_readme_dep_link),
    ("K-01 关键词覆盖空", check_k01_keyword_coverage),
    ("C-01/C-04 AUTO 区段配对", check_c01_auto_segment_pairs),
    ("C-03 path schema", check_c03_path_schema),
    ("C-05 domains 互引", check_c05_domain_consistency),
    ("AUTO 区段哈希漂移", check_auto_segment_hash_drift),
]

#: 契约子集（harness validate --contract playbook-layout 复用）
_CONTRACT_CHECKS = [
    ("C-01/C-04 AUTO 区段配对", check_c01_auto_segment_pairs),
    ("C-03 path schema", check_c03_path_schema),
    ("C-05 domains 互引", check_c05_domain_consistency),
]


def playbook_check(
    root: str | Path,
    dry_run: bool = False,
    strict: bool = False,
    contract_only: bool = False,
) -> int:
    """路书漂移检测主函数。

    Args:
        root: 仓库根目录
        dry_run: True = 仅打印，不改变任何状态（check 本身只读，dry_run 无特殊含义，保留接口兼容）
        strict: True = 任何 issue（含 K-01 警告）均 exit 1
        contract_only: True = 仅跑契约校验子集（C-01/C-03/C-05），供 validate --contract 使用

    Returns:
        0 = 无漂移，1 = 有漂移
    """
    root = Path(root).resolve()
    playbook_root = root / PLAYBOOK_ROOT_SUFFIX

    if not playbook_root.is_dir():
        print(
            f"[playbook-check] WARN: 路书目录 {PLAYBOOK_ROOT_SUFFIX} 不存在，"
            "无路书无漂移，跳过检测（exit 0）",
            file=sys.stderr,
        )
        return 0

    checks_to_run = _CONTRACT_CHECKS if contract_only else _ALL_CHECKS

    total_issues: list[tuple[str, str]] = []  # [(check_name, issue_msg)]

    for check_name, check_fn in checks_to_run:
        try:
            result = check_fn(root, playbook_root)
        except Exception as exc:
            print(f"[playbook-check] ERROR: {check_name} 检测异常: {exc}", file=sys.stderr)
            continue
        if not result.passed:
            for issue in result.issues:
                total_issues.append((check_name, issue))

    if not total_issues:
        print(f"playbook-check PASS: 0 drift detected（路书健康）")
        return 0

    # 有漂移：按类别分组打印
    # K-01 折叠逻辑（chg-B polish-2）：≥ 3 个命中时折叠为一行
    k01_issues = [issue for name, issue in total_issues if name == "K-01 关键词覆盖空"]
    non_k01_issues = [(name, issue) for name, issue in total_issues if name != "K-01 关键词覆盖空"]

    # 计算有效 fail 数（不含 K-01，K-01 是 warn 不阻断）
    fail_count = len(non_k01_issues)
    if k01_issues and not strict:
        # K-01 在非 strict 模式下是 warn
        pass
    else:
        fail_count += len(k01_issues)

    print(f"playbook-check FAIL: {len(total_issues)} drift detected")
    print()

    # 分组 non-K-01 issues
    by_check: dict[str, list[str]] = {}
    for check_name, issue in non_k01_issues:
        by_check.setdefault(check_name, []).append(issue)

    for check_name, issues in by_check.items():
        print(f"[{check_name}]")
        for i, issue in enumerate(issues[:10]):
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... +{len(issues) - 10} more")
        print()

    # K-01 折叠输出
    if k01_issues:
        if len(k01_issues) <= 2:
            # 逐条列出（≤ 2 个保持现状）
            print("[K-01 关键词覆盖空]")
            for issue in k01_issues:
                print(f"  - {issue}")
            print()
        else:
            # ≥ 3 个：折叠为一行
            domain_names = []
            for issue in k01_issues:
                # 提取 domain 名称（"empty keywords (K-01): {domain}/README.md ..."）
                import re as _re
                m = _re.match(r"empty keywords \(K-01\): ([^/]+)/", issue)
                if m:
                    domain_names.append(m.group(1))
                else:
                    domain_names.append(issue[:30])
            preview = ", ".join(domain_names[:5])
            extra = f" ..." if len(domain_names) > 5 else ""
            print(
                f"empty keywords (K-01): {len(k01_issues)} domains README ## 职责描述 仍是 TODO 占位"
                f"（建议跑 install 不带 --no-llm 或 agent 接力填写 LLM 区段）。"
                f"命中清单：{preview}{extra}"
            )
            print()

    print("建议：跑 `harness playbook-refresh` 刷新 AUTO 区段；手动修复引用失效 + 依赖链接。")

    # K-01 不阻断 exit code（除非 --strict）
    if non_k01_issues:
        return 1
    if strict and k01_issues:
        return 1
    return 0


# ---------------------------------------------------------------------------
# CLI 入口（tool script 形式）
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="路书漂移检测（req-55（项目路书Playbook体系）/ chg-05）",
    )
    parser.add_argument("--root", default=".", help="仓库根目录")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="打印检测结果，不写盘（check 本身只读，保留接口兼容）",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：任何 issue（含 K-01 警告）均 exit 1",
    )
    parser.add_argument(
        "--contract-only",
        action="store_true",
        help="仅跑契约校验子集（C-01/C-03/C-05），供 harness validate --contract playbook-layout 使用",
    )
    args = parser.parse_args(argv)
    return playbook_check(
        args.root,
        dry_run=args.dry_run,
        strict=args.strict,
        contract_only=args.contract_only,
    )


if __name__ == "__main__":
    sys.exit(main())
