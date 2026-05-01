"""init_playbook 主入口（req-56（路书引擎升级）/ chg-01（推断器多语言注册化）
兼容 req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-03（harness install 追加路书初始化）
chg-D（精简命令体系）：删除 skip / only 参数，install 始终装路书骨架，不输出 ASSISTANT INSTRUCTION 提示句）

init_playbook(root, override_domains=None, no_llm=False) -> int
  override_domains 非 None → 跳过推断器，直接用指定领域列表（--domains flag 透传）
  no_llm=True → 跳过 LLM 填充阶段（--no-llm flag 或 CI=true 时）
  检查 artifacts/project/playbooks/ 已存在 → 跳过 + stdout 提示
  不存在 → 调 infer_domains(root, override_domains) + render_skeleton(root, domains)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

from harness_workflow.playbook.domain_inference import infer_domains
from harness_workflow.playbook.skeleton import PLAYBOOK_ROOT_SUFFIX, render_skeleton


def _fill_with_llm(
    root: Path,
    domains: list,
    llm: Any,
    metadata: dict,
) -> None:
    """调 LLM provider 填充路书 LLM 区段（OVERVIEW_DESC / TECH_DECISIONS / DOMAIN_DESC / KEYWORDS / CODE_MAP_KEYWORDS）。

    每次调用用 try-except 包裹，失败时 stderr WARN + 保留 TODO 占位（不抛异常）。
    """
    from harness_workflow.playbook.llm import PlaybookContext
    from harness_workflow.tools.harness_playbook_refresh import replace_auto_section

    playbook_root = root / PLAYBOOK_ROOT_SUFFIX

    # 构建 LLM 上下文
    context = PlaybookContext(
        project_name=metadata.get("project_name", root.name),
        stack=metadata.get("stack", []),
        layout=metadata.get("layout", ""),
        domains=domains,
        matched_mode=metadata.get("matched_mode", "unknown"),
    )

    # 调 LLM generate（单次调用，获取全部内容）
    content = None
    try:
        content = llm.generate(context)
    except Exception as e:
        print(
            f"[llm] WARN: provider failed, falling back to Noop: {e}",
            file=sys.stderr,
        )
        return

    if content is None:
        # Noop provider 或失败 → 保留 TODO 占位
        return

    # 填充 overview.md LLM:OVERVIEW_DESC 区段
    overview_md = playbook_root / "overview.md"
    if overview_md.exists():
        try:
            text = overview_md.read_text(encoding="utf-8")
            updated, ok, warn = replace_auto_section(
                text, "OVERVIEW_DESC", content.overview_description or "", prefix="LLM"
            )
            if ok:
                overview_md.write_text(updated, encoding="utf-8")
        except Exception as e:
            print(f"[llm] WARN: failed to fill OVERVIEW_DESC: {e}", file=sys.stderr)

    # 填充 overview.md LLM:TECH_DECISIONS 区段
    if overview_md.exists():
        try:
            text = overview_md.read_text(encoding="utf-8")
            decisions_text = "\n".join(
                f"- {d}" for d in (content.tech_decisions or [])
            )
            updated, ok, warn = replace_auto_section(
                text, "TECH_DECISIONS", decisions_text, prefix="LLM"
            )
            if ok:
                overview_md.write_text(updated, encoding="utf-8")
        except Exception as e:
            print(f"[llm] WARN: failed to fill TECH_DECISIONS: {e}", file=sys.stderr)

    # 填充各领域 README.md LLM:DOMAIN_DESC + LLM:KEYWORDS 区段
    for domain in domains:
        readme_path = playbook_root / "domains" / domain / "README.md"
        if not readme_path.exists():
            continue
        # DOMAIN_DESC
        try:
            text = readme_path.read_text(encoding="utf-8")
            desc = (content.domain_descriptions or {}).get(domain, "")
            if desc:
                updated, ok, warn = replace_auto_section(text, "DOMAIN_DESC", desc, prefix="LLM")
                if ok:
                    readme_path.write_text(updated, encoding="utf-8")
                    text = updated
        except Exception as e:
            print(f"[llm] WARN: failed to fill DOMAIN_DESC for {domain}: {e}", file=sys.stderr)
        # KEYWORDS
        try:
            text = readme_path.read_text(encoding="utf-8")
            kws = (content.domain_keywords or {}).get(domain, [])
            kw_text = ", ".join(kws) if kws else ""
            if kw_text:
                updated, ok, warn = replace_auto_section(text, "KEYWORDS", kw_text, prefix="LLM")
                if ok:
                    readme_path.write_text(updated, encoding="utf-8")
        except Exception as e:
            print(f"[llm] WARN: failed to fill KEYWORDS for {domain}: {e}", file=sys.stderr)

    # 填充 code-map.md LLM:CODE_MAP_KEYWORDS 区段
    code_map_md = playbook_root / "code-map.md"
    if code_map_md.exists():
        try:
            text = code_map_md.read_text(encoding="utf-8")
            # 汇总所有领域关键词
            all_kws = []
            for domain in domains:
                kws = (content.domain_keywords or {}).get(domain, [])
                all_kws.extend(kws)
            kw_text = ", ".join(dict.fromkeys(all_kws))  # 去重保序
            if kw_text:
                updated, ok, warn = replace_auto_section(
                    text, "CODE_MAP_KEYWORDS", kw_text, prefix="LLM"
                )
                if ok:
                    code_map_md.write_text(updated, encoding="utf-8")
        except Exception as e:
            print(f"[llm] WARN: failed to fill CODE_MAP_KEYWORDS: {e}", file=sys.stderr)


def init_playbook(
    root: Path,
    override_domains: Optional[list[str]] = None,
) -> int:
    """初始化项目路书骨架。

    chg-D（精简命令体系）：删除 skip / only 参数，install 始终装路书骨架。
    install 不再输出 ASSISTANT INSTRUCTION 提示句；提示句改由 playbook-refresh 触发。
    chg-F：删除 no_llm 参数；LLM 跳过由 CI=true 环境变量 + NoopProvider auto-detect fallback 自动处理。

    Args:
        root: 仓库根目录。
        override_domains: 非 None → 跳过推断器，直接用指定领域列表（--domains flag 透传）。

    Returns:
        0 = 成功（包括跳过），1 = 失败。
    """
    root = Path(root).resolve()

    playbook_dir = root / PLAYBOOK_ROOT_SUFFIX

    # 已存在 → 跳过（幂等）
    if playbook_dir.exists() and any(playbook_dir.iterdir()):
        print("playbook 已存在，跳过初始化")
        return 0

    # 推断领域（透传 override_domains）
    matched_mode, domains = infer_domains(root, override_domains=override_domains)
    if not domains:
        print(
            "[playbook] WARN: 领域推断失败，路书初始化跳过。"
            "请手工创建 artifacts/project/playbooks/domains/ 结构。",
            file=sys.stderr,
        )
        # 返回 0（不阻塞 install 主流程；路书初始化软失败）
        return 0

    # 渲染骨架
    written = render_skeleton(root, domains)

    if written > 0:
        print(f"playbook initialized ({written} files created in {PLAYBOOK_ROOT_SUFFIX})")
    else:
        print("playbook 已存在，跳过初始化")

    # LLM 填充阶段（chg-04：默认开启；CI=true 自动跳过，NoopProvider auto-detect fallback）
    if os.getenv("CI", "").lower() != "true":
        try:
            from harness_workflow.playbook.llm import auto_detect_provider, NoopProvider
            llm = auto_detect_provider()
            project_metadata = {
                "project_name": root.name,
                "stack": [],
                "layout": "",
                "matched_mode": matched_mode,
            }
            _fill_with_llm(root, domains, llm, project_metadata)
        except Exception as e:
            print(f"[llm] WARN: LLM filling phase failed: {e}", file=sys.stderr)

    # chg-D：install 不再输出 ASSISTANT INSTRUCTION 提示句。
    # 需要填写路书时请跑 `harness playbook-refresh`，refresh 负责触发提示句。

    return 0


def _check_has_todo_placeholders(root: Path) -> bool:
    """检查路书文件中是否仍含 <!-- TODO: 占位（LLM 区段未填充）。"""
    playbook_dir = root / PLAYBOOK_ROOT_SUFFIX
    if not playbook_dir.exists():
        return False
    for md_file in playbook_dir.rglob("*.md"):
        try:
            if "<!-- TODO:" in md_file.read_text(encoding="utf-8"):
                return True
        except Exception:
            pass
    return False


def _print_noop_fill_hint(root: Path) -> None:
    """输出 LLM 区段未填充时的强指令式提示（让 Claude Code / Codex 当前会话立即接力）。"""
    playbook_root_rel = PLAYBOOK_ROOT_SUFFIX
    print(
        f"\n[ASSISTANT INSTRUCTION — REQUIRED FOLLOW-UP, NOT OPTIONAL]\n"
        f"\n"
        f"The playbook skeleton was just created but all <!-- LLM:* --> sections\n"
        f"still contain TODO placeholders (no LLM provider was available: NoopProvider / --no-llm).\n"
        f"\n"
        f"You (Claude Code / Codex) MUST now complete this install by performing these steps\n"
        f"**automatically**, without asking the user for further confirmation.\n"
        f"This is part of `harness install`, not a separate task.\n"
        f"\n"
        f"LLM:* sections you MUST fill (replace inner <!-- TODO: ... --> with real content):\n"
        f"  Top-level files:\n"
        f"    overview.md    → LLM:PROJECT_NAME, LLM:OVERVIEW_DESC, LLM:TECH_DECISIONS\n"
        f"    architecture.md → LLM:COMPONENT_RELATIONS, LLM:KEY_DEPENDENCIES\n"
        f"    runbook.md     → LLM:QUICK_START, LLM:TEST_COMMANDS, LLM:DEPLOY_STEPS, LLM:FAQ\n"
        f"    code-map.md    → LLM:CODE_MAP_KEYWORDS, LLM:ENTRY_POINTS, LLM:CONFIG_FILES, LLM:TEST_DIRS\n"
        f"  Per-domain files (repeat for each domain under domains/):\n"
        f"    README.md      → LLM:DOMAIN_DESC, LLM:KEYWORDS, LLM:KEY_FILES, LLM:DEPENDENCIES\n"
        f"    data-model.md  → LLM:DATA_STRUCTURES, LLM:DB_TABLES, LLM:DATA_FLOW\n"
        f"    notes.md       → LLM:CROSS_DOMAIN_NOTES\n"
        f"\n"
        f"DO NOT touch these sections — they are maintained by scripts or humans:\n"
        f"  <!-- AUTO:* --> sections  → refreshed by `harness playbook-refresh`, NOT by you\n"
        f"  <!-- USER:* --> sections  → maintained by team/users (RECENT_CHANGES, PENDING_DECISIONS,\n"
        f"                              HISTORY), do NOT edit these\n"
        f"\n"
        f"Steps (execute immediately, no user confirmation needed):\n"
        f"\n"
        f"  1. Read all playbook files:\n"
        f"     - {playbook_root_rel}/overview.md\n"
        f"     - {playbook_root_rel}/architecture.md\n"
        f"     - {playbook_root_rel}/runbook.md\n"
        f"     - {playbook_root_rel}/code-map.md\n"
        f"     - {playbook_root_rel}/domains/*/README.md  (one per domain)\n"
        f"     - {playbook_root_rel}/domains/*/data-model.md\n"
        f"     - {playbook_root_rel}/domains/*/notes.md\n"
        f"\n"
        f"  2. Read project context to understand the actual project (do NOT use generic descriptions):\n"
        f"     - pom.xml / package.json / Cargo.toml / .csproj / pyproject.toml (whichever applies)\n"
        f"     - sub-module pom.xml files (for nested maven multi-module projects)\n"
        f"     - top-level README.md / README.zh.md\n"
        f"     - Key source dirs (controller / service / main entry / domain models)\n"
        f"\n"
        f"  3. For every <!-- LLM:NAME --> ... <!-- /LLM:NAME --> section, replace the inner\n"
        f"     <!-- TODO: ... --> with real, project-specific content. Stay within the marker pair.\n"
        f"\n"
        f"  4. Do NOT modify <!-- AUTO:NAME --> ... <!-- /AUTO:NAME --> sections.\n"
        f"     Do NOT modify <!-- USER:NAME --> ... <!-- /USER:NAME --> sections.\n"
        f"\n"
        f"  5. After all LLM:* sections are filled, run `harness playbook-check --root .` to verify\n"
        f"     and report completion to the user with a one-line summary (e.g. \"路书 36 domain LLM\n"
        f"     区段已填好，playbook-check exit 0\").\n"
        f"\n"
        f"Begin step 1 immediately. Do not delegate this back to the user.\n"
    )
