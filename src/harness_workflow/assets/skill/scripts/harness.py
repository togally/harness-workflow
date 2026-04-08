#!/usr/bin/env python3
"""Standalone Harness workflow CLI for repository scaffolding and work artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "assets" / "templates"
SKILL_ROOT = Path(__file__).resolve().parents[1]
HARNESS_DIR = Path(".codex") / "harness"
MANAGED_STATE_PATH = HARNESS_DIR / "managed-files.json"
CONFIG_PATH = HARNESS_DIR / "config.json"

DEFAULT_LANGUAGE = "english"
DEFAULT_CONFIG = {"language": DEFAULT_LANGUAGE, "current_version": ""}
LANGUAGE_ALIASES = {
    "english": "english",
    "en": "english",
    "cn": "cn",
    "zh": "cn",
    "chinese": "cn",
}
DEFAULT_RUNTIME = {
    "current_version": "",
    "executing_version": "",
    "active_versions": {},
}
DEFAULT_VERSION_META = {
    "id": "",
    "title": "",
    "status": "draft",
    "stage": "idle",
    "current_task": "",
    "next_action": "",
    "current_artifact_kind": "",
    "current_artifact_id": "",
    "suggested_skill": "",
    "assistant_prompt": "",
    "approval_required": False,
    "completed_tasks": [],
    "pending_tasks": [],
    "requirement_ids": [],
    "change_ids": [],
}
WORKFLOW_RUNTIME_PATH = Path("docs") / "context" / "rules" / "workflow-runtime.yaml"
WORKFLOW_SEQUENCE = [
    "requirement_review",
    "changes_review",
    "plan_review",
    "ready_for_execution",
    "executing",
    "done",
]
LANGUAGE_SPECS = {
    "english": {
        "requirements_dir": "requirements",
        "changes_dir": "changes",
        "plans_dir": "plans",
        "version_memory": "version-memory.md",
    },
    "cn": {
        "requirements_dir": "需求",
        "changes_dir": "变更",
        "plans_dir": "计划",
        "version_memory": "版本记忆.md",
    },
}


def normalize_language(value: str | None) -> str:
    if not value:
        return DEFAULT_LANGUAGE
    normalized = LANGUAGE_ALIASES.get(value.strip().lower())
    if not normalized:
        supported = ", ".join(sorted(LANGUAGE_ALIASES))
        raise SystemExit(f"Unsupported language: {value}. Supported values: {supported}")
    return normalized


def language_spec(language: str) -> dict[str, str]:
    return LANGUAGE_SPECS[normalize_language(language)]


def template_name(name: str, language: str) -> str:
    if normalize_language(language) == "english":
        english_name = name.replace(".tmpl", ".en.tmpl")
        if (TEMPLATE_ROOT / english_name).is_file():
            return english_name
    return name


def render_template(name: str, repo_name: str, language: str, replacements: dict[str, str] | None = None) -> str:
    text = (TEMPLATE_ROOT / template_name(name, language)).read_text(encoding="utf-8")
    mapping = {
        "{{REPO_NAME}}": repo_name,
        "{{DATE}}": date.today().isoformat(),
        "{{LANGUAGE}}": normalize_language(language),
    }
    if replacements:
        mapping.update({f"{{{{{key}}}}}": value for key, value in replacements.items()})
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def write_if_missing(path: Path, content: str, created: list[str], skipped: list[str]) -> None:
    if path.exists():
        skipped.append(str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(str(path))


def _copy_tree(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def _project_skill_targets(root: Path) -> list[Path]:
    return [
        root / ".codex" / "skills" / "harness",
        root / ".claude" / "skills" / "harness",
    ]


def _managed_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json(path: Path, default: dict[str, str]) -> dict[str, str]:
    if not path.exists():
        return dict(default)
    data = json.loads(path.read_text(encoding="utf-8"))
    merged = dict(default)
    merged.update({str(key): str(value) for key, value in data.items()})
    return merged


def load_config(root: Path) -> dict[str, str]:
    config = _load_json(root / CONFIG_PATH, DEFAULT_CONFIG)
    config["language"] = normalize_language(config.get("language"))
    config["current_version"] = config.get("current_version", "").strip()
    return config


def save_config(root: Path, config: dict[str, str]) -> None:
    path = root / CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(DEFAULT_CONFIG)
    payload.update(config)
    payload["language"] = normalize_language(payload.get("language"))
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_config(root: Path) -> dict[str, str]:
    config = load_config(root)
    save_config(root, config)
    return config


def load_runtime(root: Path) -> dict[str, object]:
    path = root / WORKFLOW_RUNTIME_PATH
    if not path.exists():
        return dict(DEFAULT_RUNTIME)
    data = json.loads(path.read_text(encoding="utf-8"))
    payload = dict(DEFAULT_RUNTIME)
    payload.update(data)
    if not isinstance(payload.get("active_versions"), dict):
        payload["active_versions"] = {}
    return payload


def save_runtime(root: Path, runtime: dict[str, object]) -> None:
    path = root / WORKFLOW_RUNTIME_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(DEFAULT_RUNTIME)
    payload.update(runtime)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_managed_state(root: Path) -> dict[str, str]:
    path = root / MANAGED_STATE_PATH
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in data.get("managed_files", {}).items()}


def _save_managed_state(root: Path, managed_files: dict[str, str]) -> None:
    path = root / MANAGED_STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"managed_files": dict(sorted(managed_files.items()))}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _required_dirs(root: Path) -> list[Path]:
    return [
        root / "docs" / "context" / "team",
        root / "docs" / "context" / "project",
        root / "docs" / "context" / "experience",
        root / "docs" / "context" / "rules",
        root / "docs" / "versions" / "active",
        root / "docs" / "versions" / "archive",
        root / "docs" / "decisions",
        root / "docs" / "runbooks",
        root / "docs" / "templates",
        root / "docs" / "memory",
        root / "tools",
        root / HARNESS_DIR,
    ]


def _managed_file_contents(root: Path, language: str, include_agents: bool, include_claude: bool) -> dict[str, str]:
    repo_name = root.name
    managed = {
        "docs/README.md": render_template("docs-README.md.tmpl", repo_name, language),
        "docs/memory/constitution.md": render_template("constitution.md.tmpl", repo_name, language),
        "docs/context/experience/index.md": render_template("experience-index.md.tmpl", repo_name, language),
        "docs/context/rules/agent-workflow.md": render_template("agent-workflow.md.tmpl", repo_name, language),
        "docs/context/rules/development-flow.md": render_template("development-flow.md.tmpl", repo_name, language),
        "docs/context/rules/risk-rules.md": render_template("risk-rules.md.tmpl", repo_name, language),
        "docs/context/project/project-overview.md": render_template("project-overview.md.tmpl", repo_name, language),
        "docs/context/team/development-standards.md": render_template("development-standards.md.tmpl", repo_name, language),
        "docs/templates/requirement.md": render_template("requirement.md.tmpl", repo_name, language),
        "docs/templates/requirement-changes.md": render_template("requirement-changes.md.tmpl", repo_name, language),
        "docs/templates/change.md": render_template("change.md.tmpl", repo_name, language),
        "docs/templates/change-requirement.md": render_template("change-requirement.md.tmpl", repo_name, language),
        "docs/templates/change-design.md": render_template("change-design.md.tmpl", repo_name, language),
        "docs/templates/change-plan.md": render_template("change-plan.md.tmpl", repo_name, language),
        "docs/templates/change-acceptance.md": render_template("change-acceptance.md.tmpl", repo_name, language),
        "docs/templates/session-memory.md": render_template("session-memory.md.tmpl", repo_name, language),
        "docs/templates/version-readme.md": render_template("version-readme.md.tmpl", repo_name, language),
        "docs/templates/version-memory.md": render_template("version-memory.md.tmpl", repo_name, language),
        "tools/lint_harness_repo.py": (Path(__file__).resolve().parents[0] / "lint_harness_repo.py").read_text(encoding="utf-8"),
    }
    if include_agents:
        managed["AGENTS.md"] = render_template("AGENTS.md.tmpl", repo_name, language)
    if include_claude:
        managed["CLAUDE.md"] = render_template("CLAUDE.md.tmpl", repo_name, language)
    return managed


def _refresh_managed_state(root: Path, managed_contents: dict[str, str], existing_state: dict[str, str] | None = None) -> dict[str, str]:
    state = dict(existing_state or {})
    for relative, content in managed_contents.items():
        path = root / relative
        if path.exists() and path.read_text(encoding="utf-8") == content:
            state[relative] = _managed_hash(content)
    return state


def _install_local_skills(root: Path) -> None:
    for target in _project_skill_targets(root):
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        _copy_tree(SKILL_ROOT, target)


def ensure_harness_root(root: Path) -> dict[str, str]:
    required = [root / "docs", root / "docs" / "context", root / "docs" / "versions" / "active"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Harness workspace is missing. Run `harness init` first. Missing: {', '.join(missing)}")
    return ensure_config(root)


def version_meta_path(root: Path, version_id: str) -> Path:
    return root / "docs" / "versions" / "active" / version_id / "meta.yaml"


def load_version_meta(root: Path, version_id: str) -> dict[str, object]:
    path = version_meta_path(root, version_id)
    if not path.exists():
        payload = dict(DEFAULT_VERSION_META)
        payload["id"] = version_id
        payload["title"] = version_id
        return payload
    data = json.loads(path.read_text(encoding="utf-8"))
    payload = dict(DEFAULT_VERSION_META)
    payload.update(data)
    return payload


def save_version_meta(root: Path, version_id: str, meta: dict[str, object]) -> None:
    path = version_meta_path(root, version_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(DEFAULT_VERSION_META)
    payload.update(meta)
    payload["id"] = version_id
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_workflow_state(root: Path) -> tuple[dict[str, str], dict[str, object]]:
    config = ensure_harness_root(root)
    runtime = load_runtime(root)
    save_runtime(root, runtime)
    return config, runtime


def sync_runtime_version(root: Path, version_id: str, meta: dict[str, object], runtime: dict[str, object] | None = None) -> dict[str, object]:
    runtime_payload = dict(runtime or load_runtime(root))
    active_versions = dict(runtime_payload.get("active_versions", {}))
    active_versions[version_id] = {
        "status": str(meta.get("status", "draft")),
        "stage": str(meta.get("stage", "idle")),
        "current_task": str(meta.get("current_task", "")),
        "next_action": str(meta.get("next_action", "")),
        "current_artifact_kind": str(meta.get("current_artifact_kind", "")),
        "current_artifact_id": str(meta.get("current_artifact_id", "")),
        "suggested_skill": str(meta.get("suggested_skill", "")),
        "approval_required": bool(meta.get("approval_required", False)),
    }
    runtime_payload["active_versions"] = active_versions
    return runtime_payload


def persist_workflow_state(root: Path, version_id: str, meta: dict[str, object], runtime: dict[str, object]) -> None:
    save_version_meta(root, version_id, meta)
    runtime["current_version"] = version_id
    save_runtime(root, sync_runtime_version(root, version_id, meta, runtime))


def select_focus_change(meta: dict[str, object]) -> str:
    current_kind = str(meta.get("current_artifact_kind", ""))
    current_id = str(meta.get("current_artifact_id", ""))
    if current_kind in {"change", "plan"} and current_id:
        return current_id
    change_ids = [str(item) for item in meta.get("change_ids", [])]
    return change_ids[-1] if change_ids else ""


def apply_stage_transition(meta: dict[str, object], *, execute: bool = False, fast_forward: bool = False) -> dict[str, object]:
    payload = dict(meta)
    stage = str(payload.get("stage", "idle"))
    requirement_id = str(payload.get("current_artifact_id", "")) if str(payload.get("current_artifact_kind", "")) == "requirement" else ""
    focus_change = select_focus_change(payload)

    if fast_forward:
        payload.update(
            {
                "stage": "ready_for_execution",
                "status": "review",
                "current_task": "Confirm whether to start implementation",
                "next_action": "Run `harness next --execute` after the final review.",
                "suggested_skill": "",
                "assistant_prompt": "Review the current requirement, changes, and plan documents. Do not start coding until the human confirms execution.",
                "approval_required": True,
            }
        )
        return payload

    if stage == "requirement_review":
        payload.update(
            {
                "stage": "changes_review",
                "status": "review",
                "current_task": f"Split reviewed requirement {requirement_id or '(current requirement)'} into changes",
                "next_action": "Create or refine change documents, then run `harness next`.",
                "suggested_skill": "brainstorming",
                "assistant_prompt": f"Use brainstorming to decompose the approved requirement into independently deliverable changes, create or update the change documents, and stop for human review before advancing.",
                "approval_required": True,
            }
        )
        return payload

    if stage == "changes_review":
        if not focus_change:
            raise SystemExit("No changes exist yet. Create at least one `harness change` before advancing.")
        payload.update(
            {
                "stage": "plan_review",
                "status": "review",
                "current_task": f"Draft and review the plan for change {focus_change}",
                "next_action": f"Generate or review the plan for {focus_change}, then run `harness next`.",
                "current_artifact_kind": "change",
                "current_artifact_id": focus_change,
                "suggested_skill": "writing-plans",
                "assistant_prompt": f"Use writing-plans to turn change {focus_change} into a model-executable implementation plan, then stop for human review.",
                "approval_required": True,
            }
        )
        return payload

    if stage == "plan_review":
        payload.update(
            {
                "stage": "ready_for_execution",
                "status": "review",
                "current_task": "Review complete. Waiting for execution confirmation",
                "next_action": "Run `harness next --execute` to start implementation.",
                "suggested_skill": "",
                "assistant_prompt": "Ask the human to confirm execution. Do not start implementation before explicit confirmation.",
                "approval_required": True,
            }
        )
        return payload

    if stage == "ready_for_execution":
        if not execute:
            raise SystemExit("Current version is ready_for_execution. Run `harness next --execute` to confirm execution.")
        payload.update(
            {
                "stage": "executing",
                "status": "executing",
                "current_task": f"Execute approved work for {focus_change or 'the current version'}",
                "next_action": "Implement the approved plan and keep version state updated.",
                "current_artifact_kind": "change" if focus_change else str(payload.get("current_artifact_kind", "")),
                "current_artifact_id": focus_change or str(payload.get("current_artifact_id", "")),
                "suggested_skill": "executing-plans",
                "assistant_prompt": "Use executing-plans or subagent-driven-development to implement the approved plan. Keep documents and verification in sync while executing.",
                "approval_required": False,
            }
        )
        return payload

    if stage == "executing":
        payload.update(
            {
                "stage": "done",
                "status": "done",
                "current_task": "Execution finished. Summarize and verify outcomes",
                "next_action": "Review the implementation result and archive or continue as needed.",
                "suggested_skill": "verification-before-completion",
                "assistant_prompt": "Run final verification, summarize what changed, and capture any reusable lessons before closing the version.",
                "approval_required": False,
            }
        )
        return payload

    raise SystemExit("No workflow stage is active yet. Start with `harness requirement <title>`.")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")


def resolve_artifact_id(title: str, language: str) -> str:
    title = title.strip()
    if normalize_language(language) == "cn":
        return title
    slug = slugify(title)
    if slug:
        return slug
    fallback = re.sub(r"\s+", "-", title).strip("-")
    return fallback or title


def resolve_title_and_id(positional: str | None, id_flag: str | None, title_flag: str | None, language: str) -> tuple[str, str]:
    if positional:
        title = positional.strip()
        return title, resolve_artifact_id(title, language)
    if title_flag:
        title = title_flag.strip()
        return title, (id_flag.strip() if id_flag else resolve_artifact_id(title, language))
    if id_flag:
        identifier = id_flag.strip()
        return identifier, identifier
    raise SystemExit("A title or id is required.")


def resolve_version_layout(root: Path, version_id: str, language: str) -> dict[str, Path]:
    spec = language_spec(language)
    version_dir = root / "docs" / "versions" / "active" / version_id
    return {
        "version_dir": version_dir,
        "requirements_dir": version_dir / spec["requirements_dir"],
        "changes_dir": version_dir / spec["changes_dir"],
        "plans_dir": version_dir / spec["plans_dir"],
        "version_memory": version_dir / spec["version_memory"],
    }


def list_existing_versions(root: Path) -> list[str]:
    active_dir = root / "docs" / "versions" / "active"
    if not active_dir.exists():
        return []
    return sorted(path.name for path in active_dir.iterdir() if path.is_dir())


def active_version_instruction(root: Path, version_id: str = "") -> str:
    if version_id:
        return f'Run `harness active "{version_id}"`.'
    version_ids = list_existing_versions(root)
    if len(version_ids) == 1:
        return f'Run `harness active "{version_ids[0]}"`.'
    if version_ids:
        choices = ", ".join(f"`{item}`" for item in version_ids)
        return f"Run `harness active <version>` for one of: {choices}."
    return "Run `harness version <name>` first."


def workflow_blockers(root: Path, config: dict[str, str], runtime: dict[str, object]) -> list[str]:
    blockers: list[str] = []
    version_ids = list_existing_versions(root)
    if not version_ids:
        return blockers

    runtime_version = str(runtime.get("current_version", "")).strip()
    config_version = str(config.get("current_version", "")).strip()

    if runtime_version != config_version:
        if runtime_version and config_version:
            blockers.append(
                f"workflow runtime points to `{runtime_version}` but harness config points to `{config_version}`. "
                f"{active_version_instruction(root)}"
            )
        else:
            missing_side = "workflow runtime" if not runtime_version else "harness config"
            selected = config_version or runtime_version
            blockers.append(
                f"{missing_side} is missing the active version while `{selected}` exists elsewhere. "
                f"{active_version_instruction(root, selected)}"
            )

    effective_version = runtime_version or config_version
    if not effective_version:
        blockers.append(f"workflow routing has no active version. {active_version_instruction(root)}")
        return blockers

    if effective_version not in version_ids:
        blockers.append(
            f"active version `{effective_version}` does not exist under `docs/versions/active/`. "
            f"{active_version_instruction(root)}"
        )
        return blockers

    if not version_meta_path(root, effective_version).exists():
        blockers.append(
            f"active version `{effective_version}` is missing `meta.yaml`. Restore or recreate the version, then "
            f"{active_version_instruction(root, effective_version)}"
        )
    return blockers


def require_active_version_id(root: Path, config: dict[str, str], runtime: dict[str, object] | None = None) -> str:
    runtime_payload = dict(runtime or load_runtime(root))
    blockers = workflow_blockers(root, config, runtime_payload)
    if blockers:
        raise SystemExit(f"Workflow is blocked: {blockers[0]}")
    return str(runtime_payload.get("current_version", "") or config.get("current_version", "")).strip()


def current_version_layout(root: Path, config: dict[str, str]) -> dict[str, Path]:
    current_version = require_active_version_id(root, config)
    return resolve_version_layout(root, current_version, config["language"])


def resolve_requirement_reference(requirements_dir: Path, reference: str, language: str) -> Path | None:
    direct = requirements_dir / reference
    if direct.exists():
        return direct
    derived = requirements_dir / resolve_artifact_id(reference, language)
    if derived.exists():
        return derived
    return None


def append_change_to_requirement(requirement_dir: Path, change_id: str, title: str) -> None:
    change_map = requirement_dir / "changes.md"
    if not change_map.exists():
        return
    line = f"- [ ] `{change_id}`: {title}\n"
    text = change_map.read_text(encoding="utf-8")
    if line not in text:
        if text.rstrip().endswith("- None yet") or text.rstrip().endswith("- 暂无"):
            text = text.replace("- None yet", line.rstrip()).replace("- 暂无", line.rstrip())
        else:
            text = text.rstrip() + "\n" + line
        change_map.write_text(text.rstrip() + "\n", encoding="utf-8")


def init_repo(root: Path, write_agents: bool, write_claude: bool) -> int:
    created: list[str] = []
    skipped: list[str] = []
    config = ensure_config(root)
    language = config["language"]
    for directory in _required_dirs(root):
        directory.mkdir(parents=True, exist_ok=True)
    managed_contents = _managed_file_contents(root, language=language, include_agents=write_agents, include_claude=write_claude)
    managed_state = _load_managed_state(root)
    for relative, content in managed_contents.items():
        write_if_missing(root / relative, content, created, skipped)
    _save_managed_state(root, _refresh_managed_state(root, managed_contents, managed_state))
    if not (root / WORKFLOW_RUNTIME_PATH).exists():
        save_runtime(root, dict(DEFAULT_RUNTIME))
        created.append(str(root / WORKFLOW_RUNTIME_PATH))

    print("Created files:")
    for path in created:
        print(f"- {path}")
    print("")
    print("Skipped existing files:")
    for path in skipped:
        print(f"- {path}")
    return 0


def update_repo(root: Path, check: bool = False, force_managed: bool = False) -> int:
    config = ensure_harness_root(root)
    language = config["language"]
    runtime = load_runtime(root)
    for directory in _required_dirs(root):
        directory.mkdir(parents=True, exist_ok=True)

    managed_contents = _managed_file_contents(root, language=language, include_agents=True, include_claude=True)
    managed_state = _load_managed_state(root)
    refreshed_state = dict(managed_state)
    actions: list[str] = []

    if check:
        actions.append("would refresh .codex/skills/harness")
        actions.append("would refresh .claude/skills/harness")
    else:
        _install_local_skills(root)
        actions.append("refreshed .codex/skills/harness")
        actions.append("refreshed .claude/skills/harness")

    for relative, content in managed_contents.items():
        path = root / relative
        desired_hash = _managed_hash(content)
        if not path.exists():
            actions.append(f"{'missing' if check else 'created'} {relative}")
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                refreshed_state[relative] = desired_hash
            continue

        current = path.read_text(encoding="utf-8")
        current_hash = _managed_hash(current)
        if current == content:
            actions.append(f"current {relative}")
            refreshed_state[relative] = desired_hash
            continue

        if managed_state.get(relative) == current_hash:
            actions.append(f"{'would update' if check else 'updated'} {relative}")
            if not check:
                path.write_text(content, encoding="utf-8")
                refreshed_state[relative] = desired_hash
            continue

        if force_managed:
            actions.append(f"{'would overwrite modified' if check else 'overwrote modified'} {relative}")
            if not check:
                path.write_text(content, encoding="utf-8")
                refreshed_state[relative] = desired_hash
            continue

        actions.append(f"skipped modified {relative}")

    if not check:
        save_config(root, config)
        _save_managed_state(root, _refresh_managed_state(root, managed_contents, refreshed_state))
        if not (root / WORKFLOW_RUNTIME_PATH).exists():
            save_runtime(root, dict(DEFAULT_RUNTIME))
            actions.append("created docs/context/rules/workflow-runtime.yaml")
            runtime = load_runtime(root)

    blockers = workflow_blockers(root, config, runtime)
    for blocker in blockers:
        actions.append(f"workflow action required: {blocker}")

    print("Update summary:")
    for action in actions:
        print(f"- {action}")
    if check:
        print("")
        print("No files were changed.")
    if blockers:
        print("")
        print("Workflow is blocked until the active version is explicitly repaired.")
        return 1
    return 0


def set_language(root: Path, language: str) -> int:
    config = ensure_config(root)
    config["language"] = normalize_language(language)
    save_config(root, config)
    print(f"Language set to {config['language']}")
    print("Run `harness update` if you want managed templates and guides to refresh in the new language.")
    return 0


def create_version(root: Path, version_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip()
    if not version_id:
        raise SystemExit("Version name is required.")
    layout = resolve_version_layout(root, version_id, config["language"])
    repo_name = root.name
    created: list[str] = []
    skipped: list[str] = []

    layout["version_dir"].mkdir(parents=True, exist_ok=True)
    layout["requirements_dir"].mkdir(parents=True, exist_ok=True)
    layout["changes_dir"].mkdir(parents=True, exist_ok=True)
    layout["plans_dir"].mkdir(parents=True, exist_ok=True)

    replacements = {"VERSION_ID": version_id}
    write_if_missing(layout["version_dir"] / "README.md", render_template("version-readme.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(layout["version_memory"], render_template("version-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    meta = load_version_meta(root, version_id)
    meta.update(
        {
            "title": version_id,
            "status": "in_progress",
            "stage": meta.get("stage", "idle") or "idle",
            "current_task": meta.get("current_task", "") or "Create or review the first requirement",
            "next_action": meta.get("next_action", "") or "Run `harness requirement <title>` to begin requirement drafting.",
            "suggested_skill": meta.get("suggested_skill", "") or "",
            "assistant_prompt": meta.get("assistant_prompt", "") or "",
            "approval_required": bool(meta.get("approval_required", False)),
        }
    )

    config["current_version"] = version_id
    save_config(root, config)
    runtime["executing_version"] = runtime.get("executing_version", "")
    persist_workflow_state(root, version_id, meta, runtime)

    print(f"Active version: {version_id}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_requirement(root: Path, name: str | None, requirement_id: str | None = None, title: str | None = None) -> int:
    config, runtime = ensure_workflow_state(root)
    repo_name = root.name
    requirement_title, resolved_id = resolve_title_and_id(name, requirement_id, title, config["language"])
    layout = current_version_layout(root, config)
    requirement_dir = layout["requirements_dir"] / resolved_id
    created: list[str] = []
    skipped: list[str] = []
    replacements = {"ID": resolved_id, "TITLE": requirement_title}

    write_if_missing(requirement_dir / "requirement.md", render_template("requirement.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(requirement_dir / "changes.md", render_template("requirement-changes.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(requirement_dir / "meta.yaml", render_template("requirement-meta.yaml.tmpl", repo_name, config["language"], replacements), created, skipped)
    version_id = str(config["current_version"])
    meta = load_version_meta(root, version_id)
    requirement_ids = [str(item) for item in meta.get("requirement_ids", [])]
    if resolved_id not in requirement_ids:
        requirement_ids.append(resolved_id)
    meta.update(
        {
            "status": "in_progress",
            "stage": "requirement_review",
            "current_task": f"Review requirement {resolved_id}",
            "next_action": "Discuss and confirm the requirement, then run `harness next` to move into change design.",
            "current_artifact_kind": "requirement",
            "current_artifact_id": resolved_id,
            "suggested_skill": "brainstorming",
            "assistant_prompt": f"Use brainstorming to draft and refine requirement {resolved_id} in its document, then stop for human review.",
            "approval_required": True,
            "requirement_ids": requirement_ids,
        }
    )
    persist_workflow_state(root, version_id, meta, runtime)

    print(f"Requirement workspace: {requirement_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_change(root: Path, name: str | None, change_id: str | None = None, title: str | None = None, requirement_id: str = "") -> int:
    config, runtime = ensure_workflow_state(root)
    repo_name = root.name
    change_title, resolved_id = resolve_title_and_id(name, change_id, title, config["language"])
    layout = current_version_layout(root, config)
    change_dir = layout["changes_dir"] / resolved_id
    created: list[str] = []
    skipped: list[str] = []

    linked_requirement = requirement_id.strip() if requirement_id else ""
    replacements = {"ID": resolved_id, "TITLE": change_title, "REQUIREMENT_ID": linked_requirement or "None"}
    if config["language"] == "cn" and not linked_requirement:
        replacements["REQUIREMENT_ID"] = "未指定"

    write_if_missing(change_dir / "change.md", render_template("change.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "design.md", render_template("change-design.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "plan.md", render_template("change-plan.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "acceptance.md", render_template("change-acceptance.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "session-memory.md", render_template("session-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "meta.yaml", render_template("change-meta.yaml.tmpl", repo_name, config["language"], replacements), created, skipped)

    if linked_requirement:
        requirement_dir = resolve_requirement_reference(layout["requirements_dir"], linked_requirement, config["language"])
        if requirement_dir:
            append_change_to_requirement(requirement_dir, resolved_id, change_title)
    version_id = str(config["current_version"])
    meta = load_version_meta(root, version_id)
    change_ids = [str(item) for item in meta.get("change_ids", [])]
    if resolved_id not in change_ids:
        change_ids.append(resolved_id)
    meta.update(
        {
            "status": "in_progress",
            "stage": "changes_review" if meta.get("stage") in {"idle", "requirement_review", "changes_review"} else meta.get("stage", "changes_review"),
            "current_task": f"Review change {resolved_id}",
            "next_action": "Discuss the change list and confirm the active change, then run `harness next`.",
            "current_artifact_kind": "change",
            "current_artifact_id": resolved_id,
            "suggested_skill": "brainstorming",
            "assistant_prompt": f"Use brainstorming to refine change {resolved_id}, fill the change document, and stop for human review.",
            "approval_required": True,
            "change_ids": change_ids,
        }
    )
    persist_workflow_state(root, version_id, meta, runtime)

    print(f"Change workspace: {change_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_plan(root: Path, change_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
    layout = current_version_layout(root, config)
    candidate = layout["changes_dir"] / change_name
    if not candidate.exists():
        candidate = layout["changes_dir"] / resolve_artifact_id(change_name, config["language"])
    if not candidate.exists():
        raise SystemExit(f"Change does not exist: {change_name}")
    version_id = str(config["current_version"])
    meta = load_version_meta(root, version_id)
    meta.update(
        {
            "status": "in_progress",
            "stage": "plan_review",
            "current_task": f"Review plan for {candidate.name}",
            "next_action": "Discuss and confirm the plan, then run `harness next` to reach execution confirmation.",
            "current_artifact_kind": "plan",
            "current_artifact_id": candidate.name,
            "suggested_skill": "writing-plans",
            "assistant_prompt": f"Use writing-plans to expand plan.md for {candidate.name}, then stop for human review.",
            "approval_required": True,
        }
    )
    persist_workflow_state(root, version_id, meta, runtime)
    print(f"Plan file: {candidate / 'plan.md'}")
    print("Use writing-plans to expand this file into model-executable development and verification steps.")
    return 0


def set_active_version(root: Path, version_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip()
    if not version_meta_path(root, version_id).exists():
        raise SystemExit(f"Version does not exist: {version_id}")
    config["current_version"] = version_id
    save_config(root, config)
    meta = load_version_meta(root, version_id)
    persist_workflow_state(root, version_id, meta, runtime)
    print(f"Current active version set to {version_id}")
    return 0


def use_version(root: Path, version_name: str) -> int:
    return set_active_version(root, version_name)


def workflow_status(root: Path) -> int:
    config, runtime = ensure_workflow_state(root)
    current_version = str(runtime.get("current_version", "") or config.get("current_version", ""))
    print(f"current_version: {current_version or '(none)'}")
    print(f"executing_version: {runtime.get('executing_version', '') or '(none)'}")
    blockers = workflow_blockers(root, config, runtime)
    if blockers:
        print("workflow_blockers:")
        for blocker in blockers:
            print(f"- {blocker}")
    if current_version:
        meta = load_version_meta(root, current_version)
        print(f"stage: {meta.get('stage', 'idle')}")
        print(f"status: {meta.get('status', 'draft')}")
        print(f"current_task: {meta.get('current_task', '') or '(none)'}")
        print(f"next_action: {meta.get('next_action', '') or '(none)'}")
        print(f"current_artifact: {meta.get('current_artifact_kind', '')}:{meta.get('current_artifact_id', '')}".rstrip(":"))
        print(f"suggested_skill: {meta.get('suggested_skill', '') or '(none)'}")
        print(f"approval_required: {bool(meta.get('approval_required', False))}")
    return 0


def workflow_next(root: Path, execute: bool = False) -> int:
    config, runtime = ensure_workflow_state(root)
    current_version = require_active_version_id(root, config, runtime)
    meta = load_version_meta(root, current_version)
    meta = apply_stage_transition(meta, execute=execute)
    runtime["executing_version"] = current_version if meta.get("stage") == "executing" else ""
    persist_workflow_state(root, current_version, meta, runtime)
    print(f"Workflow advanced to {meta['stage']}")
    return 0


def workflow_fast_forward(root: Path) -> int:
    config, runtime = ensure_workflow_state(root)
    current_version = require_active_version_id(root, config, runtime)
    meta = apply_stage_transition(load_version_meta(root, current_version), fast_forward=True)
    runtime["executing_version"] = ""
    persist_workflow_state(root, current_version, meta, runtime)
    print("Workflow advanced to ready_for_execution")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Harness workflow CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize harness docs structure.")
    init_parser.add_argument("--root", default=".", help="Repository root.")
    init_parser.add_argument("--write-agents", action="store_true", help="Create AGENTS.md if missing.")
    init_parser.add_argument("--write-claude", action="store_true", help="Create CLAUDE.md if missing.")

    update_parser = subparsers.add_parser("update", help="Refresh harness-managed files in the current repository.")
    update_parser.add_argument("--root", default=".", help="Repository root.")
    update_parser.add_argument("--check", action="store_true", help="Show what would change without writing files.")
    update_parser.add_argument("--force-managed", action="store_true", help="Overwrite managed files even if modified locally.")

    language_parser = subparsers.add_parser("language", help="Switch the repository language profile.")
    language_parser.add_argument("language", help="Language profile: english or cn.")
    language_parser.add_argument("--root", default=".", help="Repository root.")

    use_parser = subparsers.add_parser("use", help="Switch the current active version.")
    use_parser.add_argument("version", help="Version name.")
    use_parser.add_argument("--root", default=".", help="Repository root.")

    active_parser = subparsers.add_parser("active", help="Explicitly set the current active version.")
    active_parser.add_argument("version", help="Version name.")
    active_parser.add_argument("--root", default=".", help="Repository root.")

    status_parser = subparsers.add_parser("status", help="Show the current workflow runtime state.")
    status_parser.add_argument("--root", default=".", help="Repository root.")

    next_parser = subparsers.add_parser("next", help="Advance the workflow to the next review stage.")
    next_parser.add_argument("--root", default=".", help="Repository root.")
    next_parser.add_argument("--execute", action="store_true", help="Confirm execution when already ready_for_execution.")

    ff_parser = subparsers.add_parser("ff", help="Fast-forward workflow stages until execution confirmation.")
    ff_parser.add_argument("--root", default=".", help="Repository root.")

    req_parser = subparsers.add_parser("requirement", help="Create a requirement inside the active version.")
    req_parser.add_argument("title", nargs="?", help="Requirement title.")
    req_parser.add_argument("--root", default=".", help="Repository root.")
    req_parser.add_argument("--id", help="Optional explicit requirement id.")
    req_parser.add_argument("--title", dest="title_flag", help="Legacy title flag.")

    change_parser = subparsers.add_parser("change", help="Create a change inside the active version.")
    change_parser.add_argument("title", nargs="?", help="Change title.")
    change_parser.add_argument("--root", default=".", help="Repository root.")
    change_parser.add_argument("--id", help="Optional explicit change id.")
    change_parser.add_argument("--title", dest="title_flag", help="Legacy title flag.")
    change_parser.add_argument("--requirement", default="", help="Optional requirement title or id to link.")

    plan_parser = subparsers.add_parser("plan", help="Show the plan file for a change.")
    plan_parser.add_argument("change", nargs="?", help="Change title or id.")
    plan_parser.add_argument("--root", default=".", help="Repository root.")
    plan_parser.add_argument("--change", dest="change_flag", help="Legacy change id flag.")

    version_parser = subparsers.add_parser("version", help="Create or switch the active version workspace.")
    version_parser.add_argument("name", nargs="?", help="Version name.")
    version_parser.add_argument("--root", default=".", help="Repository root.")
    version_parser.add_argument("--id", dest="id_flag", help="Legacy version id flag.")

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "init":
        return init_repo(root, args.write_agents, args.write_claude)
    if args.command == "update":
        return update_repo(root, check=args.check, force_managed=args.force_managed)
    if args.command == "language":
        return set_language(root, args.language)
    if args.command == "use":
        return use_version(root, args.version)
    if args.command == "active":
        return set_active_version(root, args.version)
    if args.command == "status":
        return workflow_status(root)
    if args.command == "next":
        return workflow_next(root, execute=args.execute)
    if args.command == "ff":
        return workflow_fast_forward(root)
    if args.command == "requirement":
        return create_requirement(root, args.title, requirement_id=args.id, title=args.title_flag)
    if args.command == "change":
        return create_change(root, args.title, change_id=args.id, title=args.title_flag, requirement_id=args.requirement)
    if args.command == "plan":
        change_name = args.change or args.change_flag
        if not change_name:
            raise SystemExit("A change title or id is required.")
        return create_plan(root, change_name)
    if args.command == "version":
        version_name = args.name or args.id_flag
        if not version_name:
            raise SystemExit("A version name is required.")
        return create_version(root, version_name)
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
